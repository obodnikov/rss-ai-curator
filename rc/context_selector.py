"""Smart selection of examples for LLM context."""
import logging
from typing import List, Tuple, Dict
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans
from .database import Article
from .embedder import Embedder

logger = logging.getLogger(__name__)


class LLMContextSelector:
    """Selects best liked/disliked examples for LLM context."""
    
    def __init__(self, config: dict, embedder: Embedder):
        """Initialize context selector.
        
        Args:
            config: Application configuration dictionary
            embedder: Embedder instance
        """
        self.config = config['llm_context']
        self.embedder = embedder
        self.max_liked = self.config['max_liked_examples']
        self.max_disliked = self.config['max_disliked_examples']
    
    def select_examples(
        self,
        new_article: Article,
        all_liked: List[Article],
        all_disliked: List[Article]
    ) -> Tuple[List[Article], List[Article]]:
        """Select best examples for LLM context.
        
        Args:
            new_article: Article to rank
            all_liked: All liked articles
            all_disliked: All disliked articles
            
        Returns:
            Tuple of (selected_liked, selected_disliked)
        """
        if not all_liked and not all_disliked:
            logger.info("No feedback history, returning empty examples")
            return [], []
        
        strategy = self.config.get('selection_strategy', 'hybrid')
        
        if strategy == 'recent':
            return self._select_recent(all_liked, all_disliked)
        elif strategy == 'similar':
            return self._select_similar(new_article, all_liked, all_disliked)
        elif strategy == 'diverse':
            return self._select_diverse(all_liked, all_disliked)
        elif strategy == 'hybrid':
            return self._select_hybrid(new_article, all_liked, all_disliked)
        else:
            logger.warning(f"Unknown strategy {strategy}, using recent")
            return self._select_recent(all_liked, all_disliked)
    
    def _select_recent(
        self,
        all_liked: List[Article],
        all_disliked: List[Article]
    ) -> Tuple[List[Article], List[Article]]:
        """Select most recent examples."""
        selected_liked = sorted(
            all_liked,
            key=lambda a: a.fetched_at or datetime.min,
            reverse=True
        )[:self.max_liked]
        
        selected_disliked = sorted(
            all_disliked,
            key=lambda a: a.fetched_at or datetime.min,
            reverse=True
        )[:self.max_disliked]
        
        logger.info(
            f"Selected {len(selected_liked)} liked, "
            f"{len(selected_disliked)} disliked (recent)"
        )
        return selected_liked, selected_disliked
    
    def _select_similar(
        self,
        new_article: Article,
        all_liked: List[Article],
        all_disliked: List[Article]
    ) -> Tuple[List[Article], List[Article]]:
        """Select examples most similar to new article."""
        # Get or create embedding for new article
        new_embedding = self.embedder.get_article_embedding(new_article.id)
        if new_embedding is None:
            new_embedding = self.embedder.embed_article(new_article)
        
        # Score liked articles
        liked_scores = []
        for article in all_liked:
            embedding = self.embedder.get_article_embedding(article.id)
            if embedding is not None:
                similarity = self._cosine_similarity(new_embedding, embedding)
                liked_scores.append((article, similarity))
        
        # Score disliked articles
        disliked_scores = []
        for article in all_disliked:
            embedding = self.embedder.get_article_embedding(article.id)
            if embedding is not None:
                similarity = self._cosine_similarity(new_embedding, embedding)
                disliked_scores.append((article, similarity))
        
        # Select top similar
        selected_liked = [
            a for a, _ in sorted(
                liked_scores,
                key=lambda x: x[1],
                reverse=True
            )[:self.max_liked]
        ]
        
        selected_disliked = [
            a for a, _ in sorted(
                disliked_scores,
                key=lambda x: x[1],
                reverse=True
            )[:self.max_disliked]
        ]
        
        logger.info(
            f"Selected {len(selected_liked)} liked, "
            f"{len(selected_disliked)} disliked (similar)"
        )
        return selected_liked, selected_disliked
    
    def _select_diverse(
        self,
        all_liked: List[Article],
        all_disliked: List[Article]
    ) -> Tuple[List[Article], List[Article]]:
        """Select diverse examples using clustering."""
        n_clusters = self.config['strategies']['diverse'].get('clusters', 3)
        
        selected_liked = self._cluster_and_sample(
            all_liked,
            min(n_clusters, len(all_liked)),
            self.max_liked
        )
        
        selected_disliked = self._cluster_and_sample(
            all_disliked,
            min(n_clusters, len(all_disliked)),
            self.max_disliked
        )
        
        logger.info(
            f"Selected {len(selected_liked)} liked, "
            f"{len(selected_disliked)} disliked (diverse)"
        )
        return selected_liked, selected_disliked
    
    def _select_hybrid(
        self,
        new_article: Article,
        all_liked: List[Article],
        all_disliked: List[Article]
    ) -> Tuple[List[Article], List[Article]]:
        """Combine strategies with weighted scoring."""
        weights = self.config['strategies']
        
        # Get embedding for new article
        new_emb = self.embedder.get_article_embedding(new_article.id)
        if new_emb is None:
            new_emb = self.embedder.embed_article(new_article)
        
        # Score liked articles
        liked_scores = {}
        for article in all_liked:
            score = self._calculate_hybrid_score(
                article, new_emb, weights
            )
            liked_scores[article.id] = score
        
        # Score disliked articles
        disliked_scores = {}
        for article in all_disliked:
            score = self._calculate_hybrid_score(
                article, new_emb, weights
            )
            disliked_scores[article.id] = score
        
        # Select top scored
        selected_liked = sorted(
            all_liked,
            key=lambda a: liked_scores.get(a.id, 0),
            reverse=True
        )[:self.max_liked]
        
        selected_disliked = sorted(
            all_disliked,
            key=lambda a: disliked_scores.get(a.id, 0),
            reverse=True
        )[:self.max_disliked]
        
        logger.info(
            f"Selected {len(selected_liked)} liked, "
            f"{len(selected_disliked)} disliked (hybrid)"
        )
        return selected_liked, selected_disliked
    
    def _calculate_hybrid_score(
        self,
        article: Article,
        new_embedding: np.ndarray,
        weights: Dict
    ) -> float:
        """Calculate hybrid score for article."""
        score = 0.0
        
        # Recent score
        if weights['recent']['enabled']:
            days_old = (datetime.utcnow() - (article.fetched_at or datetime.utcnow())).days
            recency_score = 1.0 / (1.0 + days_old / 30.0)
            score += recency_score * weights['recent']['weight']
        
        # Similarity score
        if weights['similar']['enabled']:
            article_emb = self.embedder.get_article_embedding(article.id)
            if article_emb is not None:
                similarity = self._cosine_similarity(new_embedding, article_emb)
                score += similarity * weights['similar']['weight']
        
        return score
    
    def _cluster_and_sample(
        self,
        articles: List[Article],
        n_clusters: int,
        n_samples: int
    ) -> List[Article]:
        """Cluster articles and sample from each cluster."""
        if len(articles) <= n_samples or n_clusters < 1:
            return articles[:n_samples]
        
        # Get embeddings
        embeddings = []
        valid_articles = []
        
        for article in articles:
            emb = self.embedder.get_article_embedding(article.id)
            if emb is not None:
                embeddings.append(emb)
                valid_articles.append(article)
        
        if len(embeddings) <= n_samples:
            return valid_articles[:n_samples]
        
        # Cluster
        n_clusters = min(n_clusters, len(embeddings))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        
        # Sample from each cluster
        selected = []
        samples_per_cluster = max(1, n_samples // n_clusters)
        
        for cluster_id in range(n_clusters):
            cluster_articles = [
                valid_articles[i] for i, label in enumerate(labels)
                if label == cluster_id
            ]
            
            # Take most recent from cluster
            cluster_sample = sorted(
                cluster_articles,
                key=lambda a: a.fetched_at or datetime.min,
                reverse=True
            )[:samples_per_cluster]
            
            selected.extend(cluster_sample)
        
        return selected[:n_samples]
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))