"""Article cleanup and retention management."""
import logging
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy.orm import Session
from .database import Article, Feedback, LLMRanking, CleanupLog
from .embedder import Embedder

logger = logging.getLogger(__name__)


class ArticleCleanupManager:
    """Manages article retention and cleanup."""
    
    def __init__(self, config: dict, embedder: Embedder):
        """Initialize cleanup manager.
        
        Args:
            config: Application configuration dictionary
            embedder: Embedder instance for vector cleanup
        """
        self.config = config['cleanup']
        self.retention = config['cleanup']['retention']
        self.embedder = embedder
    
    def run_cleanup(self, db: Session) -> Dict:
        """Execute cleanup based on policies.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.config.get('enabled', True):
            logger.info("Cleanup is disabled")
            return {'deleted': 0}
        
        logger.info("Starting article cleanup...")
        
        stats = {
            'deleted': 0,
            'liked_kept': 0,
            'disliked_kept': 0,
            'storage_freed_mb': 0
        }
        
        # Track initial counts
        initial_count = db.query(Article).count()
        
        # 1. Time-based cleanup
        stats['deleted'] += self._cleanup_by_age(db)
        
        # 2. Count-based cleanup
        stats['deleted'] += self._cleanup_by_count(db)
        
        # 3. Update kept counts
        stats['liked_kept'] = db.query(Feedback).filter(
            Feedback.rating == 'like'
        ).count()
        stats['disliked_kept'] = db.query(Feedback).filter(
            Feedback.rating == 'dislike'
        ).count()
        
        # 4. Log cleanup
        self._log_cleanup(db, stats)
        
        logger.info(
            f"Cleanup complete: {stats['deleted']} articles deleted, "
            f"{stats['liked_kept']} liked kept, "
            f"{stats['disliked_kept']} disliked kept"
        )
        
        return stats
    
    def _cleanup_by_age(self, db: Session) -> int:
        """Remove articles based on age and feedback."""
        now = datetime.utcnow()
        deleted = 0
        
        # Neutral articles (no feedback)
        cutoff_neutral = now - timedelta(
            days=self.retention['neutral_articles_days']
        )
        
        neutral_old = db.query(Article).outerjoin(Feedback).filter(
            Feedback.id == None,
            Article.fetched_at < cutoff_neutral
        ).all()
        
        for article in neutral_old:
            self._delete_article(db, article)
            deleted += 1
        
        # Disliked articles
        cutoff_disliked = now - timedelta(
            days=self.retention['disliked_articles_days']
        )
        
        disliked_old_articles = db.query(Article).join(Feedback).filter(
            Feedback.rating == 'dislike',
            Article.fetched_at < cutoff_disliked
        ).all()
        
        for article in disliked_old_articles:
            self._delete_article(db, article)
            deleted += 1
        
        # Liked articles
        cutoff_liked = now - timedelta(
            days=self.retention['liked_articles_days']
        )
        
        liked_old_articles = db.query(Article).join(Feedback).filter(
            Feedback.rating == 'like',
            Article.fetched_at < cutoff_liked
        ).all()
        
        for article in liked_old_articles:
            self._delete_article(db, article)
            deleted += 1
        
        db.commit()
        return deleted
    
    def _cleanup_by_count(self, db: Session) -> int:
        """Enforce max count limits."""
        deleted = 0
        
        # Check liked count
        liked_articles = db.query(Article).join(Feedback).filter(
            Feedback.rating == 'like'
        ).order_by(Article.fetched_at.asc()).all()
        
        liked_count = len(liked_articles)
        if liked_count > self.retention['max_liked_articles']:
            excess = liked_count - self.retention['max_liked_articles']
            deleted += self._remove_excess(
                db,
                liked_articles,
                excess,
                'like'
            )
        
        # Check disliked count
        disliked_articles = db.query(Article).join(Feedback).filter(
            Feedback.rating == 'dislike'
        ).order_by(Article.fetched_at.asc()).all()
        
        disliked_count = len(disliked_articles)
        if disliked_count > self.retention['max_disliked_articles']:
            excess = disliked_count - self.retention['max_disliked_articles']
            deleted += self._remove_excess(
                db,
                disliked_articles,
                excess,
                'dislike'
            )
        
        return deleted
    
    def _remove_excess(
        self,
        db: Session,
        articles: list,
        excess: int,
        rating_type: str
    ) -> int:
        """Remove excess articles using configured strategy."""
        strategy = self.retention.get('cleanup_strategy', 'oldest_first')
        
        if strategy == 'oldest_first':
            # Already sorted by fetched_at ascending
            to_delete = articles[:excess]
        
        elif strategy == 'lowest_rated':
            # Sort by LLM score
            articles_with_scores = []
            for article in articles:
                ranking = db.query(LLMRanking).filter(
                    LLMRanking.article_id == article.id
                ).order_by(LLMRanking.created_at.desc()).first()
                
                score = ranking.score if ranking else 0
                articles_with_scores.append((article, score))
            
            # Sort by score and take lowest
            articles_with_scores.sort(key=lambda x: x[1])
            to_delete = [a for a, _ in articles_with_scores[:excess]]
        
        else:
            # Default to oldest
            to_delete = articles[:excess]
        
        # Delete selected articles
        deleted = 0
        for article in to_delete:
            self._delete_article(db, article)
            deleted += 1
        
        db.commit()
        return deleted
    
    def _delete_article(self, db: Session, article: Article):
        """Delete article and its embeddings.
        
        Args:
            db: Database session
            article: Article to delete
        """
        # Delete from vector DB
        self.embedder.delete_article_embedding(article.id)
        
        # Delete from SQL (cascades to feedback and rankings)
        db.delete(article)
        
        logger.debug(f"Deleted article {article.id}: {article.title[:50]}...")
    
    def _log_cleanup(self, db: Session, stats: Dict):
        """Log cleanup statistics.
        
        Args:
            db: Database session
            stats: Cleanup statistics
        """
        log_entry = CleanupLog(
            articles_deleted=stats['deleted'],
            liked_kept=stats['liked_kept'],
            disliked_kept=stats['disliked_kept'],
            storage_freed_mb=stats.get('storage_freed_mb', 0)
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Cleanup log entry created: {stats['deleted']} deleted")