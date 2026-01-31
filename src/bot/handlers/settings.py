"""Telegram bot handlers for user settings and threshold configuration."""

import logging
from inspect import isawaitable
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.utils.rate_limiter import rate_limit

# Import global user settings service instance
import src.bot.services.user_settings as user_settings_module


logger = logging.getLogger(__name__)


async def _reply(update: Update, text: str) -> None:
    message = update.message or update.effective_message
    if not message:
        return
    result = message.reply_text(text)
    if isawaitable(result):
        await result


@rate_limit(seconds=3)
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command - display current threshold settings.

    Args:
        update: Telegram update object.
        context: Telegram context object.
    """
    if not update.effective_user or not (update.message or update.effective_message):
        logger.warning("settings_handler called without effective user/message")
        return

    chat_id = update.effective_user.id
    user_service = user_settings_module.user_settings_service

    try:
        user = await user_service.get_user(chat_id)

        if user is None:
            await _reply(
                update,
                "❌ User not found.\n\nPlease start the bot first with /start"
            )
            return

        # Format settings message
        message = f"""⚙️ Your Alert Settings

💧 Humidity Thresholds:
• Minimum: {user.humidity_min:.1f}%
• Maximum: {user.humidity_max:.1f}%

🔔 Alert Behavior:
• You'll be notified when humidity goes outside this range
• Cooldown: 5 minutes between similar alerts
• Recovery notifications when humidity normalizes

To change settings:
/set_humidity_min <value>
/set_humidity_max <value>

Example: /set_humidity_min 35"""

        await _reply(update, message)
        logger.info(f"Settings displayed for user {chat_id}")

    except Exception as e:
        logger.error(f"Error displaying settings for user {chat_id}: {e}", exc_info=True)
        await _reply(update, "❌ Unable to retrieve settings. Please try again.")


@rate_limit(seconds=3)
async def set_humidity_min_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /set_humidity_min command - set minimum humidity threshold.

    Args:
        update: Telegram update object.
        context: Telegram context object with args.
    """
    if not update.effective_user or not (update.message or update.effective_message):
        logger.warning("set_humidity_min_handler called without effective user/message")
        return

    chat_id = update.effective_user.id
    user_service = user_settings_module.user_settings_service

    # Check if value parameter provided
    if not context.args:
        await _reply(
            update,
            "❌ Missing humidity value.\n\n"
            "Usage: /set_humidity_min <value>\n"
            "Example: /set_humidity_min 35\n\n"
            "Value must be between 0 and 100."
        )
        return

    try:
        # Parse value
        try:
            value = float(context.args[0])
        except ValueError:
            await _reply(
                update,
                "❌ Invalid value format.\n\n"
                "Please provide a number between 0 and 100.\n"
                "Example: /set_humidity_min 35"
            )
            return

        # Validate range
        if value < 0 or value > 100:
            await _reply(
                update,
                "❌ Invalid value.\n\n"
                "Humidity must be between 0 and 100.\n"
                "Please try again.\n\n"
                "Example: /set_humidity_min 35"
            )
            return

        # Get current user settings
        user = await user_service.get_user(chat_id)
        if user is None:
            await _reply(
                update,
                "❌ User not found.\n\nPlease start the bot first with /start"
            )
            return

        # Validate min < max constraint
        if value >= user.humidity_max:
            await _reply(
                update,
                f"❌ Invalid value.\n\n"
                f"Minimum ({value:.1f}%) must be less than maximum ({user.humidity_max:.1f}%).\n"
                f"Current maximum: {user.humidity_max:.1f}%\n\n"
                f"Please set a lower minimum, or increase maximum first:\n"
                f"/set_humidity_max <value>"
            )
            return

        # Update threshold
        await user_service.update_user_threshold(
            chat_id=chat_id, humidity_min=value, humidity_max=user.humidity_max
        )

        # Confirm update
        message = f"""✅ Minimum humidity threshold updated!

New settings:
• Minimum: {value:.1f}%
• Maximum: {user.humidity_max:.1f}%

You'll now receive alerts when humidity falls below {value:.1f}%."""

        await _reply(update, message)
        logger.info(f"User {chat_id} set humidity_min to {value:.1f}%")

    except Exception as e:
        logger.error(f"Error setting humidity_min for user {chat_id}: {e}", exc_info=True)
        await _reply(update, "❌ Unable to update settings. Please try again.")


@rate_limit(seconds=3)
async def set_humidity_max_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /set_humidity_max command - set maximum humidity threshold.

    Args:
        update: Telegram update object.
        context: Telegram context object with args.
    """
    if not update.effective_user or not (update.message or update.effective_message):
        logger.warning("set_humidity_max_handler called without effective user/message")
        return

    chat_id = update.effective_user.id
    user_service = user_settings_module.user_settings_service

    # Check if value parameter provided
    if not context.args:
        await _reply(
            update,
            "❌ Missing humidity value.\n\n"
            "Usage: /set_humidity_max <value>\n"
            "Example: /set_humidity_max 70\n\n"
            "Value must be between 0 and 100."
        )
        return

    try:
        # Parse value
        try:
            value = float(context.args[0])
        except ValueError:
            await _reply(
                update,
                "❌ Invalid value format.\n\n"
                "Please provide a number between 0 and 100.\n"
                "Example: /set_humidity_max 70"
            )
            return

        # Validate range
        if value < 0 or value > 100:
            await _reply(
                update,
                "❌ Invalid value.\n\n"
                "Humidity must be between 0 and 100.\n"
                "Please try again.\n\n"
                "Example: /set_humidity_max 70"
            )
            return

        # Get current user settings
        user = await user_service.get_user(chat_id)
        if user is None:
            await _reply(
                update,
                "❌ User not found.\n\nPlease start the bot first with /start"
            )
            return

        # Validate max > min constraint
        if value <= user.humidity_min:
            await _reply(
                update,
                f"❌ Invalid value.\n\n"
                f"Maximum ({value:.1f}%) must be greater than minimum ({user.humidity_min:.1f}%).\n"
                f"Current minimum: {user.humidity_min:.1f}%\n\n"
                f"Please set a higher maximum, or decrease minimum first:\n"
                f"/set_humidity_min <value>"
            )
            return

        # Update threshold
        await user_service.update_user_threshold(
            chat_id=chat_id, humidity_min=user.humidity_min, humidity_max=value
        )

        # Confirm update
        message = f"""✅ Maximum humidity threshold updated!

New settings:
• Minimum: {user.humidity_min:.1f}%
• Maximum: {value:.1f}%

You'll now receive alerts when humidity exceeds {value:.1f}%."""

        await _reply(update, message)
        logger.info(f"User {chat_id} set humidity_max to {value:.1f}%")

    except Exception as e:
        logger.error(f"Error setting humidity_max for user {chat_id}: {e}", exc_info=True)
        await _reply(update, "❌ Unable to update settings. Please try again.")
