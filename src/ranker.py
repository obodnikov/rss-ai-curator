"""LLM-based article ranking."""
import os
import logging
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
from anthropic import Anthropic
from .database import Article, Feedback, LLMRanking
from .embedder import Embedder
from .context_selector import LLMContextSelector

logger = logging.getLogger(__name__)


class ArticleRanker:
    """Ranks articles using LLM."""
    
    def __init__(self, config: dict, embedder: Embedder):
        """Initialize article ranker.
        
        Args:
            config: Application configuration dictionary
            embedder: Embedder instance
        """
        self.config = config
        self.embedder = embedder
        self.context_selector = LLMContextSelector(config, embedder)
        
        # Initialize LLM clients
        self.provider = config['llm']['provider']
        
        if self.provider == 'chatgpt':
            api_key = os.getenv(config['llm']['chatgpt']['api_key_env'])
            self.openai_client = OpenAI(api_key=api_key)
            self.model = config['llm']['chatgpt']['model']
        elif self.provider == 'claude':
            api_key = os.getenv(config['llm']['claude']['api_key_env'])
            self.anthropic_client = Anthropic(api_key=api_key)
            self.model = config['llm']['claude']['model']
        
        logger.info(f"Ranker initialized with {self.provider} ({self.model})")
    
    def rank_article(
        self,
        db: Session,
        article: Article,
        liked_articles: List[Article],
        disliked_articles: List[Article]
    ) -> Tuple[float, str]:
        """Rank a single article.
        
        Args:
            db: Database session
            article: Article to rank
            liked_articles: User's liked articles
            disliked_articles: User's disliked articles
            
        Returns:
            Tuple of (score, reasoning)
        """
        # Select best examples for context
        selected_liked, selected_disliked = self.context_selector.select_examples(
            article, liked_articles, disliked_articles
        )
        
        # Build prompt
        prompt = self._build_prompt(
            article, selected_liked, selected_disliked
        )
        
        # Get LLM response
        score, reasoning = self._query_llm(prompt)
        
        # Save ranking
        ranking = LLMRanking(
            article_id=article.id,
            provider=self.provider,
            model=self.model,
            score=score,
            reasoning=reasoning
        )
        db.add(ranking)
        db.commit()
        
        logger.debug(f"Ranked article {article.id}: score={score}")
        return score, reasoning
    
    def _build_prompt(
        self,
        article: Article,
        liked: List[Article],
        disliked: List[Article]
    ) -> str:
        """Build ranking prompt.
        
        Args:
            article: Article to rank
            liked: Selected liked articles
            disliked: Selected disliked articles
            
        Returns:
            Formatted prompt string
        """
        # Get language settings
        language = self.config['llm'].get('response_language', 'English')
        length = self.config['llm'].get('response_length', 'concise')
        
        # Length instructions
        length_instruction = {
            'concise': '1 concise sentence (max 15 words)',
            'medium': '2 sentences (max 30 words total)',
            'detailed': '3-4 sentences with detailed reasoning'
        }.get(length, '1 concise sentence (max 15 words)')
        
        prompt = "You are a personalized news curator. "
        prompt += "Your task is to rate how relevant a new article is to the user "
        prompt += "based on their past preferences.\n\n"
        
        # Add liked examples
        if liked:
            prompt += "USER'S LIKED ARTICLES:\n"
            for i, a in enumerate(liked, 1):
                prompt += f"{i}. Title: {a.title}\n"
                summary = a.summary or a.content[:200]
                prompt += f"   Summary: {summary}\n"
                prompt += f"   Source: {a.source}\n\n"
        
        # Add disliked examples
        if disliked:
            prompt += "USER'S DISLIKED ARTICLES:\n"
            for i, a in enumerate(disliked, 1):
                prompt += f"{i}. Title: {a.title}\n"
                summary = a.summary or a.content[:200]
                prompt += f"   Summary: {summary}\n"
                prompt += f"   Source: {a.source}\n\n"
        
        # Add new article
        prompt += "NEW ARTICLE TO RATE:\n"
        prompt += f"Title: {article.title}\n"
        prompt += f"Source: {article.source}\n"
        content_preview = article.content[:1000] if article.content else article.summary
        prompt += f"Content: {content_preview}\n\n"
        
        # Add instructions with language specification
        prompt += "TASK:\n"
        prompt += "1. Rate this article from 0-10 based on the user's preferences\n"
        prompt += f"2. Provide {length_instruction} explaining why the user might (or might not) like this\n"
        prompt += f"3. Write your explanation ONLY in {language}\n\n"
        prompt += "Format your response as:\n"
        prompt += "SCORE: [number]\n"
        prompt += f"REASONING: [explanation in {language}]"
        
        return prompt
    
    def _query_llm(self, prompt: str) -> Tuple[float, str]:
        """Query LLM for ranking.
        
        Args:
            prompt: Ranking prompt
            
        Returns:
            Tuple of (score, reasoning)
        """
        try:
            if self.provider == 'chatgpt':
                return self._query_chatgpt(prompt)
            elif self.provider == 'claude':
                return self._query_claude(prompt)
            else:
                logger.error(f"Unknown LLM provider: {self.provider}")
                return 5.0, f"Unknown provider: {self.provider}"
        except Exception as e:
            logger.error(f"Error querying LLM ({self.provider}): {e}", exc_info=True)
            return 5.0, f"Error during ranking: {str(e)}"
    
    def _query_chatgpt(self, prompt: str) -> Tuple[float, str]:
        """Query ChatGPT.
        
        Args:
            prompt: Ranking prompt
            
        Returns:
            Tuple of (score, reasoning)
        """
        temperature = self.config['llm']['chatgpt'].get('temperature', 0.7)
        max_tokens = self.config['llm']['chatgpt'].get('max_tokens', 500)
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a personalized news curator."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        return self._parse_response(content)
    
    def _query_claude(self, prompt: str) -> Tuple[float, str]:
        """Query Claude.
        
        Args:
            prompt: Ranking prompt
            
        Returns:
            Tuple of (score, reasoning)
        """
        temperature = self.config['llm']['claude'].get('temperature', 0.7)
        max_tokens = self.config['llm']['claude'].get('max_tokens', 500)
        
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        return self._parse_response(content)
    
    def _parse_response(self, content: str) -> Tuple[float, str]:
        """Parse LLM response.
        
        Args:
            content: LLM response text
            
        Returns:
            Tuple of (score, reasoning)
        """
        score = 5.0
        reasoning = ""
        
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SCORE:'):
                score_str = line.replace('SCORE:', '').strip()
                try:
                    score = float(score_str)
                    # Clamp to 0-10
                    score = max(0.0, min(10.0, score))
                except ValueError:
                    logger.warning(f"Could not parse score: {score_str}")
            
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()
        
        if not reasoning:
            reasoning = content[:200]
        
        return score, reasoning
    
    def filter_and_rank_candidates(
        self,
        db: Session,
        new_articles: List[Article],
        liked_articles: List[Article],
        disliked_articles: List[Article]
    ) -> List[Tuple[Article, float, str]]:
        """Filter and rank candidate articles.
        
        Args:
            db: Database session
            new_articles: New articles to evaluate
            liked_articles: User's liked articles
            disliked_articles: User's disliked articles
            
        Returns:
            List of (article, score, reasoning) tuples, sorted by score
        """
        if not new_articles:
            logger.warning("filter_and_rank_candidates: No new articles provided")
            return []
        
        logger.info(
            f"Starting ranking: {len(new_articles)} new articles, "
            f"{len(liked_articles)} liked, {len(disliked_articles)} disliked"
        )
        
        # Step 1: Embedding-based filtering
        try:
            candidates = self._filter_by_similarity(
                new_articles, liked_articles, disliked_articles
            )
            
            logger.info(
                f"Filtered {len(new_articles)} articles to "
                f"{len(candidates)} candidates using embeddings"
            )
        except Exception as e:
            logger.error(f"Error in similarity filtering: {e}", exc_info=True)
            # Fallback: use first N articles
            limit = self.config['filtering']['top_candidates_for_llm']
            candidates = new_articles[:limit]
            logger.warning(f"Using fallback: first {len(candidates)} articles")
        
        if not candidates:
            logger.warning("No candidates after filtering")
            return []
        
        # Step 2: LLM ranking
        ranked = []
        for i, article in enumerate(candidates, 1):
            try:
                logger.debug(f"Ranking article {i}/{len(candidates)}: {article.title[:50]}...")
                score, reasoning = self.rank_article(
                    db, article, liked_articles, disliked_articles
                )
                ranked.append((article, score, reasoning))
                logger.debug(f"Article {i} scored: {score}/10")
            except Exception as e:
                logger.error(
                    f"Error ranking article {article.id} ('{article.title[:50]}...'): {e}",
                    exc_info=True
                )
                # Continue with other articles instead of failing completely
                continue
        
        if not ranked:
            logger.error(
                f"All {len(candidates)} candidates failed to rank! "
                f"Check LLM configuration and API keys."
            )
            return []
        
        # Sort by score
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        # Log detailed LLM ranking statistics
        scores = [s for _, s, _ in ranked]
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        
        # Calculate score distribution
        score_ranges = {
            '0-3': len([s for s in scores if s < 3]),
            '3-5': len([s for s in scores if 3 <= s < 5]),
            '5-7': len([s for s in scores if 5 <= s < 7]),
            '7-9': len([s for s in scores if 7 <= s < 9]),
            '9-10': len([s for s in scores if s >= 9])
        }
        
        current_threshold = self.config['filtering'].get('min_score_to_show', 7.0)
        above_threshold = len([s for s in scores if s >= current_threshold])
        
        # Calculate optimal threshold suggestions
        percentile_75 = sorted(scores)[int(len(scores) * 0.75)] if scores else 0
        percentile_90 = sorted(scores)[int(len(scores) * 0.90)] if scores else 0
        
        logger.info(
            f"📊 LLM ranking statistics:\n"
            f"  • Articles ranked: {len(ranked)}\n"
            f"  • Max score: {max_score:.1f}/10\n"
            f"  • Min score: {min_score:.1f}/10\n"
            f"  • Avg score: {avg_score:.1f}/10\n"
            f"  • Current threshold: {current_threshold:.1f}/10\n"
            f"  • Articles above threshold: {above_threshold}/{len(ranked)}\n"
            f"\n"
            f"  Score distribution:\n"
            f"    0-3: {score_ranges['0-3']} articles\n"
            f"    3-5: {score_ranges['3-5']} articles\n"
            f"    5-7: {score_ranges['5-7']} articles\n"
            f"    7-9: {score_ranges['7-9']} articles\n"
            f"    9-10: {score_ranges['9-10']} articles\n"
            f"\n"
            f"  💡 Threshold suggestions:\n"
            f"    • For top 25%: {percentile_75:.1f}\n"
            f"    • For top 10%: {percentile_90:.1f}\n"
            f"    • For guaranteed articles: {max(min_score, max_score - 1.0):.1f}\n"
        )
        
        if above_threshold == 0 and ranked:
            logger.warning(
                f"⚠️ No articles passed threshold {current_threshold:.1f}/10!\n"
                f"   Highest score was {max_score:.1f}/10\n"
                f"   💡 Recommendation: Lower min_score_to_show to {max(3.0, max_score - 0.5):.1f}"
            )
        
        logger.info(
            f"Ranking complete: {len(ranked)}/{len(candidates)} articles ranked successfully"
        )
        
        return ranked
    def _filter_by_similarity(
        self,
        new_articles: List[Article],
        liked_articles: List[Article],
        disliked_articles: List[Article]
    ) -> List[Article]:
        """
        Filter articles by embedding similarity with balanced source selection.
        
        This prevents high-volume sources from dominating the LLM input.
        """
        if not liked_articles and not disliked_articles:
            limit = self.config['filtering']['top_candidates_for_llm']
            logger.info(f"No training data - returning first {limit} articles")
            return new_articles[:limit]
        
        threshold = self.config['filtering']['similarity_threshold']
        scored_articles = []
        
        # Calculate similarity scores
        for article in new_articles:
            embedding = self.embedder.get_article_embedding(article.id)
            if embedding is None:
                embedding = self.embedder.embed_article(article)
                self.embedder.store_article_embedding(article, embedding)
            
            # Calculate liked similarity
            liked_sims = []
            for liked in liked_articles:
                liked_emb = self.embedder.get_article_embedding(liked.id)
                if liked_emb is not None:
                    sim = self._cosine_similarity(embedding, liked_emb)
                    liked_sims.append(sim)
            
            # Calculate disliked similarity
            disliked_sims = []
            for disliked in disliked_articles:
                disliked_emb = self.embedder.get_article_embedding(disliked.id)
                if disliked_emb is not None:
                    sim = self._cosine_similarity(embedding, disliked_emb)
                    disliked_sims.append(sim)
            
            # Combined score
            liked_score = sum(liked_sims) / len(liked_sims) if liked_sims else 0
            disliked_score = sum(disliked_sims) / len(disliked_sims) if disliked_sims else 0
            combined_score = liked_score - 0.3 * disliked_score
            
            if combined_score >= threshold:
                scored_articles.append({
                    'article': article,
                    'score': combined_score,
                    'source': article.source
                })
        
        # Log statistics
        if scored_articles:
            scores = [item['score'] for item in scored_articles]
            logger.info(
                f"📊 Similarity stats: {len(scored_articles)}/{len(new_articles)} above {threshold:.3f}\n"
                f"  • Max: {max(scores):.3f}, Avg: {sum(scores)/len(scores):.3f}"
            )
        
        # ✨ NEW: Balanced selection by source
        selected = self._select_balanced_by_source(
            scored_articles,
            self.config['filtering']['top_candidates_for_llm']
        )
        
        return selected

    def _select_balanced_by_source(
        self,
        scored_articles: List[dict],
        target_count: int
    ) -> List[Article]:
        """Select articles ensuring balanced source representation."""
        if not scored_articles:
            return []
        
        from collections import defaultdict
        
        # Group by source
        by_source = defaultdict(list)
        for item in scored_articles:
            by_source[item['source']].append(item)
        
        # Sort each source by score
        for source in by_source:
            by_source[source].sort(key=lambda x: x['score'], reverse=True)
        
        # Calculate quota
        num_sources = len(by_source)
        quota_per_source = max(1, target_count // num_sources)
        
        # First pass: balanced selection
        selected_items = []
        for source, items in by_source.items():
            take_count = min(quota_per_source, len(items))
            selected_items.extend(items[:take_count])
        
        # Second pass: fill remaining with best scores
        if len(selected_items) < target_count:
            remaining = []
            for source, items in by_source.items():
                remaining.extend(items[quota_per_source:])
            remaining.sort(key=lambda x: x['score'], reverse=True)
            needed = target_count - len(selected_items)
            selected_items.extend(remaining[:needed])
        
        # Sort by score and extract articles
        selected_items.sort(key=lambda x: x['score'], reverse=True)
        selected_articles = [item['article'] for item in selected_items[:target_count]]
        
        # Log distribution
        distribution = defaultdict(int)
        for item in selected_items[:target_count]:
            distribution[item['source']] += 1
        
        logger.info(f"📊 Balanced selection: {len(selected_articles)} articles")
        for source, count in sorted(distribution.items()):
            logger.info(f"  • {source}: {count} articles")
        
        return selected_articles
    
