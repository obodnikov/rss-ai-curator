"""RSS AI Curator - A personalized RSS feed aggregator with AI ranking."""

__version__ = '1.0.0'
__author__ = 'Michael Obodnikov'
__description__ = 'AI-powered RSS feed aggregator with preference learning'

from .database import DatabaseManager, Article, Feedback, LLMRanking, CleanupLog
from .fetcher import RSSFetcher
from .embedder import Embedder
from .ranker import ArticleRanker
from .context_selector import LLMContextSelector
from .cleanup import ArticleCleanupManager
from .telegram_bot import TelegramBot
from .scheduler import AppScheduler

__all__ = [
    'DatabaseManager',
    'Article',
    'Feedback',
    'LLMRanking',
    'CleanupLog',
    'RSSFetcher',
    'Embedder',
    'ArticleRanker',
    'LLMContextSelector',
    'ArticleCleanupManager',
    'TelegramBot',
    'AppScheduler',
]