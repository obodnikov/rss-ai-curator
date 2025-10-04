"""LLM-based article ranking."""
import os
import logging
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
        
        # Add instructions
        prompt += "TASK:\n"
        prompt += "1. Rate this article from 0-10 based on the user's preferences\n"
        prompt += "2. Provide 1-2 sentences explaining why the user might (or might not) like this\n\n"
        prompt += "Format your response as:\n"
        prompt += "SCORE: [number]\n"
        prompt += "REASONING: [explanation]"
        
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
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            return 5.0, "Error during ranking"
    
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
            return []
        
        # Step 1: Embedding-based filtering
        candidates = self._filter_by_similarity(
            new_articles, liked_articles, disliked_articles
        )
        
        logger.info(
            f"Filtered {len(new_articles)} articles to "
            f"{len(candidates)} candidates using embeddings"
        )
        
        # Step 2: LLM ranking
        ranked = []
        for article in candidates:
            score, reasoning = self.rank_article(
                db, article, liked_articles, disliked_articles
            )
            ranked.append((article, score, reasoning))
        
        # Sort by score
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def _filter_by_similarity(
        self,
        new_articles: List[Article],
        liked_articles: List[Article],
        disliked_articles: List[Article]
    ) -> List[Article]:
        """Filter articles by embedding similarity.
        
        Args:
            new_articles: Articles to filter
            liked_articles: Liked articles
            disliked_articles: Disliked articles
            
        Returns:
            Filtered list of articles
        """
        if not liked_articles and not disliked_articles:
            # No feedback yet, return top candidates by count
            limit = self.config['filtering']['top_candidates_for_llm']
            return new_articles[:limit]
        
        threshold = self.config['filtering']['similarity_threshold']
        candidates = []
        
        for article in new_articles:
            # Get or create embedding
            embedding = self.embedder.get_article_embedding(article.id)
            if embedding is None:
                embedding = self.embedder.embed_article(article)
                self.embedder.store_article_embedding(article, embedding)
            
            # Calculate similarity scores
            liked_sims = []
            for liked in liked_articles:
                liked_emb = self.embedder.get_article_embedding(liked.id)
                if liked_emb is not None:
                    sim = self._cosine_similarity(embedding, liked_emb)
                    liked_sims.append(sim)
            
            disliked_sims = []
            for disliked in disliked_articles:
                disliked_emb = self.embedder.get_article_embedding(disliked.id)
                if disliked_emb is not None:
                    sim = self._cosine_similarity(embedding, disliked_emb)
                    disliked_sims.append(sim)
            
            # Calculate combined score
            liked_score = sum(liked_sims) / len(liked_sims) if liked_sims else 0
            disliked_score = sum(disliked_sims) / len(disliked_sims) if disliked_sims else 0
            
            combined_score = liked_score - 0.3 * disliked_score
            
            if combined_score >= threshold:
                candidates.append((article, combined_score))
        
        # Sort by combined score and take top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        limit = self.config['filtering']['top_candidates_for_llm']
        
        return [a for a, _ in candidates[:limit]]
    
    @staticmethod
    def _cosine_similarity(vec1, vec2) -> float:
        """Calculate cosine similarity."""
        import numpy as np
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))