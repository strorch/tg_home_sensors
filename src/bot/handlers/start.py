"""Start and help command handlers."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

import src.bot.services.user_settings as user_settings_module


logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command to initialize user.
    
    Args:
        update: Telegram update.
        context: Telegram context.
    """
    if not update.effective_user or not update.message:
        return
    
    chat_id = update.effective_user.id
    
    try:
        # Check if user exists
        if user_settings_module.user_settings_service is None:
            raise RuntimeError("User settings service not initialized")

        user = await user_settings_module.user_settings_service.get_user(chat_id)
        
        if user is None:
            # Create new user with defaults
            user = await user_settings_module.user_settings_service.create_user(chat_id)
            logger.info(f"Initialized new user {chat_id}")
        
        # Send welcome message
        welcome_msg = (
            "Welcome to Arduino Home Sensors Bot! 🌡️💧\n\n"
            "I monitor your Arduino sensors and alert you when humidity levels are unusual.\n\n"
            "Available commands:\n"
            "/sensors - Get current sensor readings\n"
            "/settings - View your alert thresholds\n"
            "/set_humidity_min <value> - Set minimum humidity %\n"
            "/set_humidity_max <value> - Set maximum humidity %\n"
            "/help - Show this help message\n\n"
            "Your current thresholds:\n"
            f"• Min: {user.humidity_min}%\n"
            f"• Max: {user.humidity_max}%\n\n"
            "You'll receive alerts when humidity goes outside this range."
        )
        
        await update.message.reply_text(welcome_msg)
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, unable to initialize your account. Please try again."
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command to display help information.
    
    Args:
        update: Telegram update.
        context: Telegram context.
    """
    if not update.message:
        return
    
    help_msg = (
        "Arduino Home Sensors Bot - Help 📖\n\n"
        "📊 Monitoring Commands:\n"
        "/sensors or /status - Get current sensor readings\n\n"
        "⚙️ Configuration Commands:\n"
        "/settings - View your humidity thresholds\n"
        "/set_humidity_min <value> - Set minimum threshold (0-100)\n"
        "/set_humidity_max <value> - Set maximum threshold (0-100)\n\n"
        "ℹ️ Information:\n"
        "/help - Show this message\n"
        "/start - Initialize bot\n\n"
        "🔔 Automatic Alerts:\n"
        "You'll receive automatic notifications when:\n"
        "• Humidity exceeds your maximum threshold\n"
        "• Humidity falls below your minimum threshold\n"
        "• Humidity returns to normal range\n\n"
        "⏱️ Alert cooldown: 5 minutes between similar alerts"
    )
    
    await update.message.reply_text(help_msg)
