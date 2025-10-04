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
    
    def _register_handlers(self):
        """Register command and callback handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        
        if user_id != self.admin_user_id:
            await update.message.reply_text(
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
        
        await update.message.reply_text(welcome_msg)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_msg = (
            "📚 Available Commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/stats - Show your preference statistics\n\n"
            "The bot automatically fetches and sends articles every few hours. "
            "Just rate them with the buttons!"
        )
        
        await update.message.reply_text(help_msg)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
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
            
            await update.message.reply_text(stats_msg)
        
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
            
            # Update message with feedback indicator
            emoji = "👍" if action == "like" else "👎"
            updated_text = query.message.text + f"\n\n{emoji} Your feedback has been {feedback_msg}!"
            
            await query.edit_message_text(updated_text)
            
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
        logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop the bot."""
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Telegram bot stopped")
    
    def run_polling(self):
        """Run bot in polling mode (blocking)."""
        self.app.run_polling()