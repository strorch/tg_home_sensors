"""Sensors command handler."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

import src.bot.services.serial_reader as serial_reader_module
import src.bot.services.user_settings as user_settings_module
from src.bot.utils.rate_limiter import rate_limit


logger = logging.getLogger(__name__)


@rate_limit(seconds=3)
async def sensors_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sensors and /status commands to display current readings.
    
    Args:
        update: Telegram update.
        context: Telegram context.
    """
    if not update.effective_user or not update.message:
        return
    
    chat_id = update.effective_user.id
    
    try:
        # Get latest sensor reading
        if serial_reader_module.serial_reader_service is None:
            raise RuntimeError("Serial reader service not initialized")

        if user_settings_module.user_settings_service is None:
            raise RuntimeError("User settings service not initialized")

        reading = serial_reader_module.serial_reader_service.get_latest_reading()
        
        if reading is None:
            await update.message.reply_text(
                "❌ Sensor Unavailable\n\n"
                "The Arduino sensor is currently disconnected.\n"
                "Attempting to reconnect...\n\n"
                "Please try again in a few moments."
            )
            return
        
        # Get user settings to determine status
        user = await user_settings_module.user_settings_service.get_user(chat_id)
        if user is None:
            await update.message.reply_text(
                "Please initialize the bot first with /start"
            )
            return
        
        # Determine humidity status
        if reading.humidity > user.humidity_max:
            status = "⚠️ Status: HIGH HUMIDITY ALERT"
        elif reading.humidity < user.humidity_min:
            status = "⚠️ Status: LOW HUMIDITY ALERT"
        else:
            status = "✅ Status: Normal"
        
        # Format message
        message = (
            "📊 Current Sensor Readings\n\n"
            f"💧 Humidity: {reading.humidity:.2f}%\n"
            f"🌡️ DHT Temperature: {reading.dht_temperature:.2f}°C\n"
            f"🌡️ LM35 Temperature: {reading.lm35_temperature:.2f}°C\n"
            f"🌡️ Thermistor: {reading.thermistor_temperature:.2f}°C\n\n"
            f"📅 Last updated: {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"Your humidity thresholds: {user.humidity_min}% - {user.humidity_max}%\n"
            f"{status}"
        )
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in sensors handler: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, unable to retrieve sensor data. Please try again."
        )


# Alias for /status command
status_handler = sensors_handler
