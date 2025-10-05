"""Database models and session management."""
import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Article(Base):
    """Article model."""
    
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow, index=True)
    content_hash = Column(String(64), unique=True, index=True)
    delete_after = Column(DateTime, index=True)
    
    # NEW: Track if article was shown to user
    shown_to_user = Column(Boolean, default=False, index=True)
    shown_at = Column(DateTime)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="article", cascade="all, delete-orphan")
    rankings = relationship("LLMRanking", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"


class Feedback(Base):
    """User feedback on articles."""
    
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    rating = Column(String(20), nullable=False)  # 'like' or 'dislike'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    relevance_score = Column(Float)
    
    # Relationships
    article = relationship("Article", back_populates="feedback")
    
    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, article_id={self.article_id}, rating='{self.rating}')>"


class LLMRanking(Base):
    """LLM ranking results for articles."""
    
    __tablename__ = 'llm_rankings'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False, index=True)
    provider = Column(String(20), nullable=False)
    model = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    article = relationship("Article", back_populates="rankings")
    
    def __repr__(self) -> str:
        return f"<LLMRanking(id={self.id}, score={self.score}, provider='{self.provider}')>"


class CleanupLog(Base):
    """Cleanup operation logs."""
    
    __tablename__ = 'cleanup_log'
    
    id = Column(Integer, primary_key=True)
    cleanup_date = Column(DateTime, default=datetime.utcnow)
    articles_deleted = Column(Integer, default=0)
    liked_kept = Column(Integer, default=0)
    disliked_kept = Column(Integer, default=0)
    storage_freed_mb = Column(Float, default=0.0)
    
    def __repr__(self) -> str:
        return f"<CleanupLog(date={self.cleanup_date}, deleted={self.articles_deleted})>"


class Config(Base):
    """Application configuration storage."""
    
    __tablename__ = 'config'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Config(key='{self.key}', value='{self.value[:50]}...')>"


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: dict):
        """Initialize database manager.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        db_path = config.get('database', {}).get('path', 'data/rss_curator.db')
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        database_url = f"sqlite:///{db_path}"
        echo = config.get('database', {}).get('echo', False)
        
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=echo
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized at {db_path}")
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def get_session(self):
        """Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    def get_db_size(self) -> float:
        """Get database file size in MB.
        
        Returns:
            Size in megabytes
        """
        db_path = self.config.get('database', {}).get('path', 'data/rss_curator.db')
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            return size_bytes / (1024 * 1024)
        return 0.0
    
    def get_stats(self, session) -> dict:
        """Get database statistics.
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_articles': session.query(Article).count(),
            'shown_articles': session.query(Article).filter(
                Article.shown_to_user == True
            ).count(),
            'liked_articles': session.query(Feedback).filter(
                Feedback.rating == 'like'
            ).count(),
            'disliked_articles': session.query(Feedback).filter(
                Feedback.rating == 'dislike'
            ).count(),
            'total_cleanups': session.query(CleanupLog).count(),
            'db_size_mb': self.get_db_size()
        }
        
        # Get total deleted from cleanup logs
        cleanup_sum = session.query(
            CleanupLog
        ).with_entities(
            CleanupLog.articles_deleted
        ).all()
        stats['total_deleted'] = sum(c[0] for c in cleanup_sum)
        
        return stats
