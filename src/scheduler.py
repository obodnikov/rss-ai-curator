"""Task scheduling for RSS fetching and digest generation."""
import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from .database import DatabaseManager, Article, Feedback
from .fetcher import RSSFetcher
from .embedder import Embedder
from .ranker import ArticleRanker
from .cleanup import ArticleCleanupManager
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)


class AppScheduler:
    """Manages all scheduled tasks."""
    
    def __init__(
        self,
        config: dict,
        db_manager: DatabaseManager,
        fetcher: RSSFetcher,
        embedder: Embedder,
        ranker: ArticleRanker,
        cleanup_manager: ArticleCleanupManager,
        telegram_bot: TelegramBot
    ):
        """Initialize scheduler.
        
        Args:
            config: Application configuration
            db_manager: Database manager
            fetcher: RSS fetcher
            embedder: Embedder
            ranker: Article ranker
            cleanup_manager: Cleanup manager
            telegram_bot: Telegram bot
        """
        self.config = config
        self.db_manager = db_manager
        self.fetcher = fetcher
        self.embedder = embedder
        self.ranker = ranker
        self.cleanup_manager = cleanup_manager
        self.telegram_bot = telegram_bot
        
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start all scheduled jobs."""
        
        # RSS fetch job
        fetch_interval = self.config['scheduling']['fetch_interval_hours']
        self.scheduler.add_job(
            self._fetch_rss_job,
            IntervalTrigger(hours=fetch_interval),
            id='fetch_rss',
            name='Fetch RSS feeds',
            replace_existing=True
        )
        logger.info(f"Scheduled RSS fetch every {fetch_interval} hour(s)")
        
        # Digest generation job
        digest_interval = self.config['scheduling']['digest_interval_hours']
        self.scheduler.add_job(
            self._generate_digest_job,
            IntervalTrigger(hours=digest_interval),
            id='generate_digest',
            name='Generate article digest',
            replace_existing=True
        )
        logger.info(f"Scheduled digest generation every {digest_interval} hour(s)")
        
        # Cleanup job (daily at specified time)
        cleanup_time = self.config['scheduling'].get('cleanup_time', '03:00')
        hour, minute = map(int, cleanup_time.split(':'))
        
        self.scheduler.add_job(
            self._cleanup_job,
            CronTrigger(hour=hour, minute=minute),
            id='cleanup',
            name='Clean old articles',
            replace_existing=True
        )
        logger.info(f"Scheduled cleanup at {cleanup_time} daily")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started with all jobs")
    
    def _fetch_rss_job(self):
        """Job: Fetch RSS feeds."""
        logger.info("Starting scheduled RSS fetch...")
        db = self.db_manager.get_session()
        
        try:
            new_count = self.fetcher.fetch_all(db)
            logger.info(f"RSS fetch complete: {new_count} new articles")
        except Exception as e:
            logger.error(f"Error in RSS fetch job: {e}")
        finally:
            db.close()
    
    def _generate_digest_job(self):
        """Job: Generate and send digest."""
        logger.info("Starting digest generation...")
        db = self.db_manager.get_session()
        
        try:
            # Get pending articles (not yet rated)
            pending = db.query(Article).outerjoin(Feedback).filter(
                Feedback.id == None
            ).all()
            
            if not pending:
                logger.info("No pending articles for digest")
                return
            
            # Get user's feedback history
            liked = db.query(Article).join(Feedback).filter(
                Feedback.rating == 'like'
            ).all()
            
            disliked = db.query(Article).join(Feedback).filter(
                Feedback.rating == 'dislike'
            ).all()
            
            logger.info(
                f"Digest input: {len(pending)} pending, "
                f"{len(liked)} liked, {len(disliked)} disliked"
            )
            
            # Filter and rank articles
            ranked = self.ranker.filter_and_rank_candidates(
                db, pending, liked, disliked
            )
            
            # Apply score threshold
            min_score = self.config['filtering'].get('min_score_to_show', 7.0)
            filtered = [
                (a, s, r) for a, s, r in ranked
                if s >= min_score
            ]
            
            # Limit to articles per digest
            max_articles = self.config['filtering']['articles_per_digest']
            digest_articles = filtered[:max_articles]
            
            if digest_articles:
                # Send digest asynchronously
                asyncio.run(
                    self.telegram_bot.send_digest(digest_articles)
                )
                
                # Log summary with sent articles
                scores_sent = [s for _, s, _ in digest_articles]
                avg_score_sent = sum(scores_sent) / len(scores_sent)
                
                logger.info(
                    f"✅ Digest sent successfully!\n"
                    f"  • Articles sent: {len(digest_articles)}\n"
                    f"  • Avg score of sent articles: {avg_score_sent:.1f}/10\n"
                    f"  • Score range: {min(scores_sent):.1f} - {max(scores_sent):.1f}"
                )
            else:
                # Log detailed statistics when no articles meet threshold
                if ranked:
                    scores = [s for _, s, _ in ranked]
                    max_score = max(scores)
                    avg_score = sum(scores) / len(scores)
                    
                    logger.warning(
                        f"❌ No articles met score threshold!\n"
                        f"  • Threshold: {min_score}/10\n"
                        f"  • Max score: {max_score:.1f}/10\n"
                        f"  • Avg score: {avg_score:.1f}/10\n"
                        f"  • Ranked: {len(ranked)} articles\n"
                        f"  • Training data: {len(liked)} liked, {len(disliked)} disliked\n"
                        f"\n"
                        f"  💡 Configuration recommendations:\n"
                        f"    • Lower min_score_to_show to: {max(3.0, max_score - 0.5):.1f}\n"
                        f"    • Or wait until you have 10+ liked articles"
                    )
                    
                    if len(liked) < 5:
                        logger.info(
                            f"⚠️ Insufficient training data ({len(liked)} likes).\n"
                            f"   System needs 10-15 rated articles for better results.\n"
                            f"   Current performance is expected with limited training."
                        )
                    else:
                        logger.info(
                            f"💡 You have {len(liked)} liked articles.\n"
                            f"   Consider:\n"
                            f"   1. Lowering threshold to {max_score:.1f}\n"
                            f"   2. Adjusting RSS feeds to match your interests\n"
                            f"   3. Reviewing your liked/disliked articles for consistency"
                        )
                else:
                    logger.error(
                        f"❌ Ranking failed completely!\n"
                        f"  • Pending articles: {len(pending)}\n"
                        f"  • Articles ranked: 0\n"
                        f"  • This indicates an issue with embeddings or LLM.\n"
                        f"  • Check API keys and LLM configuration."
                    )
        
        except Exception as e:
            logger.error(f"Error in digest generation job: {e}")
        finally:
            db.close()
    
    def _cleanup_job(self):
        """Job: Run cleanup."""
        logger.info("Starting scheduled cleanup...")
        db = self.db_manager.get_session()
        
        try:
            stats = self.cleanup_manager.run_cleanup(db)
            logger.info(f"Cleanup complete: {stats}")
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
        finally:
            db.close()
    
    def run_fetch_now(self):
        """Run RSS fetch immediately."""
        logger.info("Running immediate RSS fetch...")
        self._fetch_rss_job()
    
    def run_digest_now(self):
        """Run digest generation immediately."""
        logger.info("Running immediate digest generation...")
        self._generate_digest_job()
    
    def run_cleanup_now(self):
        """Run cleanup immediately."""
        logger.info("Running immediate cleanup...")
        self._cleanup_job()
    
    def stop(self):
        """Stop scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
