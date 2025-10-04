"""RSS feed fetching and parsing."""
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from .database import Article

logger = logging.getLogger(__name__)


class RSSFetcher:
    """Fetches and parses RSS feeds."""
    
    def __init__(self, config: dict):
        """Initialize RSS fetcher.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.feeds = config.get('rss_feeds', [])
        logger.info(f"RSS Fetcher initialized with {len(self.feeds)} feeds")
    
    def fetch_all(self, db: Session) -> int:
        """Fetch articles from all configured RSS feeds.
        
        Args:
            db: Database session
            
        Returns:
            Number of new articles added
        """
        logger.info("Starting RSS fetch for all feeds...")
        total_new = 0
        
        for feed_config in self.feeds:
            try:
                new_count = self._fetch_feed(db, feed_config)
                total_new += new_count
                logger.info(
                    f"Feed '{feed_config['name']}': {new_count} new articles"
                )
            except Exception as e:
                logger.error(
                    f"Error fetching feed '{feed_config['name']}': {e}"
                )
        
        db.commit()
        logger.info(f"RSS fetch complete: {total_new} new articles total")
        return total_new
    
    def _fetch_feed(self, db: Session, feed_config: dict) -> int:
        """Fetch articles from a single RSS feed.
        
        Args:
            db: Database session
            feed_config: Feed configuration with 'url' and 'name'
            
        Returns:
            Number of new articles added
        """
        url = feed_config['url']
        source_name = feed_config['name']
        
        # Parse RSS feed
        feed = feedparser.parse(url)
        
        if feed.bozo:
            logger.warning(
                f"Feed '{source_name}' has parsing issues: {feed.bozo_exception}"
            )
        
        new_articles = 0
        
        for entry in feed.entries:
            article_data = self._parse_entry(entry, source_name)
            
            if article_data and self._save_article(db, article_data):
                new_articles += 1
        
        return new_articles
    
    def _parse_entry(self, entry, source_name: str) -> Optional[Dict]:
        """Parse a single RSS entry.
        
        Args:
            entry: Feedparser entry object
            source_name: Name of the source feed
            
        Returns:
            Dictionary with article data or None if invalid
        """
        # Extract URL
        url = entry.get('link')
        if not url:
            return None
        
        # Extract title
        title = entry.get('title', 'Untitled')
        
        # Extract content
        content = ''
        if hasattr(entry, 'content'):
            content = entry.content[0].value
        elif hasattr(entry, 'summary'):
            content = entry.summary
        elif hasattr(entry, 'description'):
            content = entry.description
        
        # Clean HTML from content
        content = self._clean_html(content)
        
        # Extract summary (first 500 chars of content)
        summary = content[:500] + '...' if len(content) > 500 else content
        
        # Extract published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except Exception:
                pass
        
        if not published_at and hasattr(entry, 'updated_parsed'):
            try:
                published_at = datetime(*entry.updated_parsed[:6])
            except Exception:
                pass
        
        # Create content hash for deduplication
        content_hash = self._hash_content(url, title, content)
        
        return {
            'url': url,
            'title': title,
            'content': content,
            'summary': summary,
            'source': source_name,
            'published_at': published_at,
            'content_hash': content_hash
        }
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and clean text.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text
        """
        if not html_content:
            return ''
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    @staticmethod
    def _hash_content(url: str, title: str, content: str) -> str:
        """Create hash of article content for deduplication.
        
        Args:
            url: Article URL
            title: Article title
            content: Article content
            
        Returns:
            SHA256 hash
        """
        combined = f"{url}{title}{content[:1000]}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _save_article(self, db: Session, article_data: dict) -> bool:
        """Save article to database if it doesn't exist.
        
        Args:
            db: Database session
            article_data: Article data dictionary
            
        Returns:
            True if new article saved, False if duplicate
        """
        # Check if article already exists (by URL or content hash)
        existing = db.query(Article).filter(
            (Article.url == article_data['url']) |
            (Article.content_hash == article_data['content_hash'])
        ).first()
        
        if existing:
            return False
        
        # Create new article
        article = Article(**article_data)
        db.add(article)
        
        try:
            db.flush()  # Get the ID without committing
            logger.debug(f"New article saved: {article.title[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            db.rollback()
            return False
    
    def fetch_single_url(self, db: Session, url: str, source_name: str = "Manual") -> Optional[Article]:
        """Fetch and save a single article from URL.
        
        Args:
            db: Database session
            url: Article URL
            source_name: Source name for the article
            
        Returns:
            Article object if successful, None otherwise
        """
        try:
            import requests
            from readability import Document
            
            # Fetch page
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract content
            doc = Document(response.text)
            title = doc.title()
            content = self._clean_html(doc.summary())
            
            article_data = {
                'url': url,
                'title': title,
                'content': content,
                'summary': content[:500] + '...' if len(content) > 500 else content,
                'source': source_name,
                'published_at': datetime.utcnow(),
                'content_hash': self._hash_content(url, title, content)
            }
            
            if self._save_article(db, article_data):
                db.commit()
                return db.query(Article).filter(
                    Article.url == url
                ).first()
            
        except Exception as e:
            logger.error(f"Error fetching single URL {url}: {e}")
        
        return None