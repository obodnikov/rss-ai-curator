"""RSS AI Curator - Main entry point."""
import os
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Disable ChromaDB telemetry BEFORE any chromadb imports
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

from src.database import DatabaseManager
from src.fetcher import RSSFetcher
from src.embedder import Embedder
from src.ranker import ArticleRanker
from src.cleanup import ArticleCleanupManager
from src.telegram_bot import TelegramBot
from src.scheduler import AppScheduler


def setup_logging(config: dict):
    """Setup logging configuration.
    
    Args:
        config: Application configuration
    """
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('file', 'logs/rss_curator.log')
    max_bytes = log_config.get('max_bytes', 10485760)  # 10MB
    backup_count = log_config.get('backup_count', 5)
    
    # Create logs directory
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    
    # Completely suppress ChromaDB telemetry
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
    logging.getLogger('chromadb.telemetry.product').setLevel(logging.CRITICAL)
    logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.CRITICAL)


def load_config() -> dict:
    """Load configuration from YAML file.
    
    Returns:
        Configuration dictionary
    """
    config_path = Path('config/config.yaml')
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Please create it from config/config.yaml.example"
        )
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


async def init_components(config: dict):
    """Initialize all application components.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of initialized components
    """
    logger = logging.getLogger(__name__)
    
    # Initialize database
    logger.info("Initializing database...")
    db_manager = DatabaseManager(config)
    db_manager.create_tables()
    
    # Initialize embedder
    logger.info("Initializing embedder...")
    embedder = Embedder(config)
    
    # Initialize fetcher
    logger.info("Initializing RSS fetcher...")
    fetcher = RSSFetcher(config)
    
    # Initialize ranker
    logger.info("Initializing article ranker...")
    ranker = ArticleRanker(config, embedder)
    
    # Initialize cleanup manager
    logger.info("Initializing cleanup manager...")
    cleanup_manager = ArticleCleanupManager(config, embedder)
    
    # Initialize Telegram bot
    logger.info("Initializing Telegram bot...")
    telegram_bot = TelegramBot(config, db_manager)
    await telegram_bot.start()
    
    # Initialize scheduler
    logger.info("Initializing scheduler...")
    scheduler = AppScheduler(
        config, db_manager, fetcher, embedder,
        ranker, cleanup_manager, telegram_bot
    )
    
    return (
        db_manager, embedder, fetcher, ranker,
        cleanup_manager, telegram_bot, scheduler
    )


async def run_init():
    """Initialize the application (create database, etc.)."""
    logger = logging.getLogger(__name__)
    
    logger.info("=== RSS AI Curator - Initialization ===")
    
    config = load_config()
    setup_logging(config)
    
    # Create data directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Initialize database
    db_manager = DatabaseManager(config)
    db_manager.create_tables()
    
    logger.info("✅ Initialization complete!")
    logger.info("You can now run: python main.py start")


async def run_app():
    """Run the main application."""
    logger = logging.getLogger(__name__)
    
    logger.info("=== RSS AI Curator - Starting ===")
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    # Initialize components
    (
        db_manager, embedder, fetcher, ranker,
        cleanup_manager, telegram_bot, scheduler
    ) = await init_components(config)
    
    # Start scheduler
    scheduler.start()
    
    logger.info("🚀 RSS AI Curator is running...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Keep the bot running
        await telegram_bot.app.updater.start_polling()
        
        # Keep main thread alive
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # Cleanup in reverse order of initialization
        try:
            logger.info("Stopping scheduler...")
            scheduler.stop()
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        try:
            logger.info("Stopping Telegram bot...")
            await telegram_bot.stop()
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
        
        logger.info("✅ RSS AI Curator stopped")

async def run_fetch():
    """Run RSS fetch once and exit."""
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    config = load_config()
    setup_logging(config)
    
    logger.info("=== Running RSS Fetch ===")
    
    db_manager = DatabaseManager(config)
    fetcher = RSSFetcher(config)
    
    db = db_manager.get_session()
    try:
        new_count = fetcher.fetch_all(db)
        logger.info(f"✅ Fetched {new_count} new articles")
    finally:
        db.close()


async def run_digest():
    """Generate and send digest once and exit."""
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    config = load_config()
    setup_logging(config)
    
    logger.info("=== Generating Digest ===")
    
    # Initialize components
    (
        db_manager, embedder, fetcher, ranker,
        cleanup_manager, telegram_bot, scheduler
    ) = await init_components(config)
    
    try:
        scheduler.run_digest_now()
        logger.info("✅ Digest generation complete")
    finally:
        await telegram_bot.stop()


async def run_cleanup():
    """Run cleanup once and exit."""
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    config = load_config()
    setup_logging(config)
    
    logger.info("=== Running Cleanup ===")
    
    db_manager = DatabaseManager(config)
    embedder = Embedder(config)
    cleanup_manager = ArticleCleanupManager(config, embedder)
    
    db = db_manager.get_session()
    try:
        stats = cleanup_manager.run_cleanup(db)
        logger.info(f"✅ Cleanup complete: {stats}")
    finally:
        db.close()


async def run_stats():
    """Show statistics and exit."""
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    config = load_config()
    setup_logging(config)
    
    db_manager = DatabaseManager(config)
    db = db_manager.get_session()
    
    try:
        stats = db_manager.get_stats(db)
        
        print("\n" + "="*50)
        print("RSS AI Curator - Statistics")
        print("="*50)
        print(f"Total articles:     {stats['total_articles']}")
        print(f"Liked articles:     {stats['liked_articles']}")
        print(f"Disliked articles:  {stats['disliked_articles']}")
        print(f"Total cleanups:     {stats['total_cleanups']}")
        print(f"Total deleted:      {stats['total_deleted']}")
        print(f"Database size:      {stats['db_size_mb']:.2f} MB")
        print("="*50 + "\n")
    
    finally:
        db.close()


def print_usage():
    """Print usage information."""
    print("""
RSS AI Curator - Usage

Commands:
  python main.py init         Initialize database and directories
  python main.py start        Start the bot (runs continuously)
  python main.py fetch        Fetch RSS feeds once
  python main.py digest       Generate and send digest once
  python main.py cleanup      Run cleanup once
  python main.py stats        Show statistics
  python main.py help         Show this help message

Examples:
  python main.py init         # First time setup
  python main.py start        # Start the bot
  python main.py fetch        # Manual RSS fetch
  python main.py stats        # Check your stats

For more information, see README.md
    """)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        asyncio.run(run_init())
    elif command == 'start':
        asyncio.run(run_app())
    elif command == 'fetch':
        asyncio.run(run_fetch())
    elif command == 'digest':
        asyncio.run(run_digest())
    elif command == 'cleanup':
        asyncio.run(run_cleanup())
    elif command == 'stats':
        asyncio.run(run_stats())
    elif command == 'help':
        print_usage()
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
