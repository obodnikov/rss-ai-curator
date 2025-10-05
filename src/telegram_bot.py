"""Telegram bot interface."""
import os
import logging
from typing import Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from .database import DatabaseManager, Article, Feedback

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for article curation."""
    
    def __init__(self, config: dict, db_manager: DatabaseManager):
        """Initialize Telegram bot.
        
        Args:
            config: Application configuration dictionary
            db_manager: Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        
        # Get bot token and admin user ID
        token = os.getenv(config['telegram']['bot_token_env'])
        admin_user_id_str = os.getenv(config['telegram']['admin_user_id_env'])
        
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        if not admin_user_id_str:
            raise ValueError("TELEGRAM_ADMIN_USER_ID not set")
        
        self.admin_user_id = int(admin_user_id_str)
        
        # Create application
        self.app = Application.builder().token(token).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info(f"Telegram bot initialized for admin user {self.admin_user_id}")
    
    async def setup_bot_commands(self):
        """Set up bot command menu in Telegram."""
        from telegram import BotCommand
        
        commands = [
            BotCommand("start", "Initialize bot"),
            BotCommand("help", "Show all commands"),
            BotCommand("stats", "Show your preference statistics"),
            BotCommand("fetch", "Fetch RSS feeds now"),
            BotCommand("digest", "Generate and send digest now"),
            BotCommand("cleanup", "Run cleanup now"),
        ]
        
        await self.app.bot.set_my_commands(commands)
        logger.info("Bot commands menu configured")
    
    def _register_handlers(self):
        """Register command and callback handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("fetch", self.fetch_command))
        self.app.add_handler(CommandHandler("digest", self.digest_command))
        self.app.add_handler(CommandHandler("cleanup", self.cleanup_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not update.effective_message:
            return
            
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            await update.effective_message.reply_text(
                "Sorry, this bot is private and only available to authorized users."
            )
            return
        
        welcome_msg = (
            "🤖 Welcome to RSS AI Curator!\n\n"
            "I'll help you discover relevant articles from your RSS feeds.\n\n"
            "How it works:\n"
            "1. I fetch articles from your configured feeds\n"
            "2. I analyze them based on your preferences\n"
            "3. I send you the most relevant ones\n"
            "4. You rate them with 👍 or 👎\n"
            "5. I learn and improve!\n\n"
            "Use /help to see all commands."
        )
        
        await update.effective_message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not update.effective_message:
            return
            
        help_msg = (
            "📚 Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/stats - Show your preference statistics\n"
            "/fetch - Fetch RSS feeds now\n"
            "/digest - Generate and send digest now\n"
            "/cleanup - Run cleanup now\n\n"
            "The bot automatically fetches and sends articles every few hours. "
            "Just rate them with the buttons!"
        )
        
        await update.effective_message.reply_text(help_msg)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        if not update.effective_message:
            return
            
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            return
        
        db = self.db_manager.get_session()
        try:
            stats = self.db_manager.get_stats(db)
            
            stats_msg = (
                "📊 Your Preference Stats\n\n"
                f"👍 Liked: {stats['liked_articles']} articles\n"
                f"👎 Disliked: {stats['disliked_articles']} articles\n"
                f"📰 Total articles: {stats['total_articles']}\n"
                f"🗑️ Cleaned up: {stats['total_deleted']} articles\n"
                f"💾 Database size: {stats['db_size_mb']:.1f} MB"
            )
            
            await update.effective_message.reply_text(stats_msg)
        
        finally:
            db.close()
    
    async def fetch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fetch command - manually trigger RSS fetch."""
        if not update.effective_message:
            return
            
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            return
        
        await update.effective_message.reply_text("🔄 Fetching RSS feeds...")
        
        # Import here to avoid circular dependency
        from .fetcher import RSSFetcher
        
        db = self.db_manager.get_session()
        try:
            fetcher = RSSFetcher(self.config)
            new_count = fetcher.fetch_all(db)
            
            await update.effective_message.reply_text(
                f"✅ Fetch complete!\n\n"
                f"📰 Found {new_count} new articles"
            )
            logger.info(f"Manual fetch triggered by user {user_id}: {new_count} new articles")
        
        except Exception as e:
            logger.error(f"Error in manual fetch: {e}")
            await update.effective_message.reply_text(
                f"❌ Error fetching feeds:\n{str(e)}"
            )
        finally:
            db.close()
    
    async def digest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /digest command - manually generate and send digest."""
        if not update.effective_message:
            return
            
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            return
        
        await update.effective_message.reply_text("🔄 Generating digest...")
        
        # Import here to avoid circular dependency
        from .ranker import ArticleRanker
        from .embedder import Embedder
        from .database import Article, Feedback
        
        db = self.db_manager.get_session()
        try:
            # Initialize components
            embedder = Embedder(self.config)
            ranker = ArticleRanker(self.config, embedder)
            
            # Get pending articles
            pending = db.query(Article).outerjoin(Feedback).filter(
                Feedback.id == None
            ).all()
            
            if not pending:
                await update.effective_message.reply_text("ℹ️ No pending articles to rank")
                return
            
            # Get user feedback history
            liked = db.query(Article).join(Feedback).filter(
                Feedback.rating == 'like'
            ).all()
            
            disliked = db.query(Article).join(Feedback).filter(
                Feedback.rating == 'dislike'
            ).all()
            
            # Filter and rank
            ranked = ranker.filter_and_rank_candidates(
                db, pending, liked, disliked
            )
            
            # Get config settings
            min_score = self.config['filtering'].get('min_score_to_show', 7.0)
            max_articles = self.config['filtering']['articles_per_digest']
            
            # Apply score threshold
            filtered = [
                (a, s, r) for a, s, r in ranked
                if s >= min_score
            ]
            
            # Limit to articles per digest
            digest_articles = filtered[:max_articles]
            
            if digest_articles:
                await self.send_digest(digest_articles)
                await update.effective_message.reply_text(
                    f"✅ Digest sent!\n\n"
                    f"📬 Sent {len(digest_articles)} articles"
                )
                logger.info(f"Manual digest triggered by user {user_id}: {len(digest_articles)} articles")
            else:
                # No articles met threshold - provide detailed feedback
                if ranked:
                    # Get score statistics
                    scores = [s for _, s, _ in ranked]
                    max_score = max(scores)
                    avg_score = sum(scores) / len(scores)
                    
                    feedback_msg = (
                        f"ℹ️ No articles met the score threshold\n\n"
                        f"📊 Statistics:\n"
                        f"• Threshold: {min_score}/10\n"
                        f"• Highest score: {max_score:.1f}/10\n"
                        f"• Average score: {avg_score:.1f}/10\n"
                        f"• Articles ranked: {len(ranked)}\n\n"
                    )
                    
                    # Provide helpful suggestions based on situation
                    if len(liked) < 5:
                        feedback_msg += (
                            f"💡 Tip: You have only {len(liked)} liked articles. "
                            f"Rate 10-15 more articles to improve recommendations!\n\n"
                            f"Temporarily lower threshold in config:\n"
                            f"<code>min_score_to_show: {max(0, min_score - 2):.1f}</code>"
                        )
                    else:
                        feedback_msg += (
                            f"💡 Suggestions:\n"
                            f"1. Lower threshold to {max_score:.1f} in config\n"
                            f"2. Adjust RSS feeds to match your interests\n"
                            f"3. Review your liked/disliked articles\n\n"
                            f"Config setting:\n"
                            f"<code>min_score_to_show: {max(0, max_score - 0.5):.1f}</code>"
                        )
                    
                    await update.effective_message.reply_text(
                        feedback_msg,
                        parse_mode='HTML'
                    )
                else:
                    # No articles were ranked at all
                    await update.effective_message.reply_text(
                        f"⚠️ Ranking failed\n\n"
                        f"• Pending articles: {len(pending)}\n"
                        f"• Articles ranked: 0\n\n"
                        f"This might indicate an issue with embeddings or LLM. "
                        f"Check logs for errors."
                    )
        
        except Exception as e:
            logger.error(f"Error in manual digest: {e}")
            await update.effective_message.reply_text(
                f"❌ Error generating digest:\n\n"
                f"<code>{str(e)}</code>\n\n"
                f"Check logs for details.",
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    async def cleanup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cleanup command - manually run cleanup."""
        if not update.effective_message:
            return
            
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            return
        
        await update.effective_message.reply_text("🗑️ Running cleanup...")
        
        # Import here to avoid circular dependency
        from .cleanup import ArticleCleanupManager
        from .embedder import Embedder
        
        db = self.db_manager.get_session()
        try:
            embedder = Embedder(self.config)
            cleanup_manager = ArticleCleanupManager(self.config, embedder)
            
            stats = cleanup_manager.run_cleanup(db)
            
            await update.effective_message.reply_text(
                f"✅ Cleanup complete!\n\n"
                f"🗑️ Deleted: {stats['deleted']} articles\n"
                f"👍 Kept liked: {stats['liked_kept']}\n"
                f"👎 Kept disliked: {stats['disliked_kept']}"
            )
            logger.info(f"Manual cleanup triggered by user {user_id}: {stats['deleted']} deleted")
        
        except Exception as e:
            logger.error(f"Error in manual cleanup: {e}")
            await update.effective_message.reply_text(
                f"❌ Error running cleanup:\n{str(e)}"
            )
        finally:
            db.close()
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if user_id != self.admin_user_id:
            return
        
        # Parse callback data: "like_123" or "dislike_123"
        data = query.data
        action, article_id_str = data.split('_')
        article_id = int(article_id_str)
        
        db = self.db_manager.get_session()
        try:
            # Get article
            article = db.query(Article).filter(
                Article.id == article_id
            ).first()
            
            if not article:
                await query.edit_message_text("Article not found.")
                return
            
            # Check if feedback already exists
            existing_feedback = db.query(Feedback).filter(
                Feedback.article_id == article_id,
                Feedback.user_id == user_id
            ).first()
            
            if existing_feedback:
                # Update existing feedback
                existing_feedback.rating = action
                existing_feedback.created_at = datetime.utcnow()
                feedback_msg = "updated"
            else:
                # Create new feedback
                feedback = Feedback(
                    article_id=article_id,
                    user_id=user_id,
                    rating=action
                )
                db.add(feedback)
                feedback_msg = "recorded"
            
            db.commit()
            
            # Keep original message text and add feedback indicator
            emoji = "👍" if action == "like" else "👎"
            original_text = query.message.text
            
            # Remove old feedback line if exists
            lines = original_text.split('\n')
            filtered_lines = [line for line in lines if not line.startswith(('👍', '👎'))]
            updated_text = '\n'.join(filtered_lines)
            
            # Add new feedback line
            updated_text += f"\n\n{emoji} Your feedback has been {feedback_msg}!"
            
            # Update message without removing buttons
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [
                    InlineKeyboardButton("👍 Like", callback_data=f"like_{article.id}"),
                    InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{article.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=updated_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            logger.info(
                f"User {user_id} rated article {article_id} as {action}"
            )
        
        finally:
            db.close()
    
    async def send_article(
        self,
        article: Article,
        score: float,
        reasoning: str
    ):
        """Send article to admin user.
        
        Args:
            article: Article to send
            score: LLM relevance score
            reasoning: LLM reasoning
        """
        # Format message
        message = self._format_article_message(article, score, reasoning)
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("👍 Like", callback_data=f"like_{article.id}"),
                InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{article.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await self.app.bot.send_message(
                chat_id=self.admin_user_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            logger.debug(f"Sent article {article.id} to user {self.admin_user_id}")
        
        except Exception as e:
            logger.error(f"Error sending article {article.id}: {e}")
    
    async def send_digest(self, articles_with_scores: list):
        """Send digest of articles.
        
        Args:
            articles_with_scores: List of (article, score, reasoning) tuples
        """
        if not articles_with_scores:
            logger.info("No articles to send in digest")
            return
        
        # Send header
        header = f"📬 <b>Article Digest</b> - {len(articles_with_scores)} articles\n"
        header += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "─" * 30
        
        try:
            await self.app.bot.send_message(
                chat_id=self.admin_user_id,
                text=header,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending digest header: {e}")
        
        # Send each article
        for article, score, reasoning in articles_with_scores:
            await self.send_article(article, score, reasoning)
        
        logger.info(f"Sent digest with {len(articles_with_scores)} articles")
    
    def _format_article_message(
        self,
        article: Article,
        score: float,
        reasoning: str
    ) -> str:
        """Format article message.
        
        Args:
            article: Article object
            score: LLM score
            reasoning: LLM reasoning
            
        Returns:
            Formatted HTML message
        """
        config = self.config['telegram']
        
        msg = ""
        
        # Score
        if config.get('show_score', True):
            msg += f"🎯 <b>Score: {score:.1f}/10</b>\n\n"
        
        # Title and link
        title = article.title[:200]
        msg += f"📰 <a href='{article.url}'>{title}</a>\n\n"
        
        # Metadata
        metadata_parts = []
        
        if config.get('show_date', True) and article.published_at:
            time_ago = self._time_ago(article.published_at)
            metadata_parts.append(f"📅 {time_ago}")
        
        if config.get('show_source', True) and article.source:
            metadata_parts.append(f"Source: {article.source}")
        
        if metadata_parts:
            msg += " | ".join(metadata_parts) + "\n\n"
        
        # Reasoning
        if config.get('show_reasoning', True) and reasoning:
            msg += f"💡 <b>Why you might like this:</b>\n"
            msg += f"<i>{reasoning}</i>"
        
        return msg
    
    @staticmethod
    def _time_ago(dt: datetime) -> str:
        """Convert datetime to human-readable time ago.
        
        Args:
            dt: Datetime object
            
        Returns:
            Human-readable string
        """
        now = datetime.utcnow()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    async def start(self):
        """Start the bot."""
        await self.app.initialize()
        await self.app.start()
        await self.setup_bot_commands()  # Set up command menu
        logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop the bot."""
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Telegram bot stopped")
    
    def run_polling(self):
        """Run bot in polling mode (blocking)."""
        self.app.run_polling()
