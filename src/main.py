"""Bot entry point."""

import asyncio
import logging
from telegram.ext import Application, CommandHandler

from src.config import load_config
from src.bot.services.database import Database
from src.bot.services.serial_reader import SerialReaderService
from src.bot.services.user_settings import UserSettingsService
from src.bot.services.alert_manager import AlertManager
from src.bot.utils.logger import setup_logging
from src.bot.handlers.start import start_handler, help_handler
from src.bot.handlers.sensors import sensors_handler, status_handler
from src.bot.handlers.settings import (
    settings_handler,
    set_humidity_min_handler,
    set_humidity_max_handler,
)

# Import global service instances
import src.bot.services.serial_reader as serial_reader_module
import src.bot.services.user_settings as user_settings_module
import src.bot.services.alert_manager as alert_manager_module


logger = logging.getLogger(__name__)


async def notify_all_users(bot, user_service: UserSettingsService, message: str) -> None:
    """Send notification message to all registered users.

    Args:
        bot: Telegram bot instance.
        user_service: User settings service.
        message: Message to send.
    """
    try:
        users = await user_service.get_all_users()
        for user in users:
            try:
                await bot.send_message(chat_id=user.chat_id, text=message)
            except Exception as e:
                logger.error(f"Failed to notify user {user.chat_id}: {e}")
    except Exception as e:
        logger.error(f"Failed to get users for notification: {e}")


async def monitoring_loop(
    serial_service: SerialReaderService,
    alert_service: AlertManager,
    user_service: UserSettingsService,
    bot,
) -> None:
    """Background task to continuously monitor sensors and send alerts.

    Args:
        serial_service: Serial reader service.
        alert_service: Alert manager service.
        user_service: User settings service.
        bot: Telegram bot instance for connection notifications.
    """
    logger.info("Starting monitoring loop")
    was_connected = serial_service.is_connected()

    while True:
        try:
            # Read sensor data
            reading = await serial_service.read_sensor_data()

            # Check connection state changes
            is_connected = serial_service.is_connected()

            if is_connected and not was_connected:
                # Connection restored
                logger.info("Arduino connection restored")
                await notify_all_users(
                    bot,
                    user_service,
                    "✅ Arduino connection restored!\n\nSensor monitoring resumed.",
                )
                was_connected = True
            elif not is_connected and was_connected:
                # Connection lost
                logger.warning("Arduino connection lost")
                await notify_all_users(
                    bot, user_service, "⚠️ Arduino connection lost!\n\nAttempting to reconnect..."
                )
                was_connected = False

            if reading is not None:
                # Get all registered users
                users = await user_service.get_all_users()

                # Check thresholds for each user
                for user in users:
                    await alert_service.process_reading(reading, user.chat_id)
            else:
                # No reading available - try to reconnect if disconnected
                if not is_connected:
                    logger.debug("Attempting to reconnect to Arduino...")
                    reconnected = await serial_service.connect()
                    if reconnected and not was_connected:
                        # First successful reconnection
                        logger.info("Arduino reconnected successfully")
                        await notify_all_users(
                            bot,
                            user_service,
                            "✅ Arduino connection restored!\n\nSensor monitoring resumed.",
                        )
                        was_connected = True

            # Wait before next reading (Arduino sends every second)
            await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            await asyncio.sleep(5)  # Wait before retrying


async def main() -> None:
    """Initialize and run the bot."""
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return

    # Setup logging
    setup_logging(config.log_level)
    logger.info("Bot starting...")

    # Initialize database
    database = Database(config.database_url)
    try:
        await database.connect()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Initialize services
    user_settings_module.user_settings_service = UserSettingsService(database)
    serial_reader_module.serial_reader_service = SerialReaderService(
        port=config.serial_port, baud_rate=config.serial_baud_rate
    )

    # Connect to Arduino
    connected = await serial_reader_module.serial_reader_service.connect()
    if connected:
        logger.info("Arduino connected successfully")
    else:
        logger.warning("Failed to connect to Arduino - will retry in background")

    # Initialize bot application
    try:
        app = Application.builder().token(config.telegram_bot_token).build()

        # Initialize alert manager with bot instance
        alert_manager_module.alert_manager = AlertManager(database=database, bot=app.bot)

        # Register handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("sensors", sensors_handler))
        app.add_handler(CommandHandler("status", status_handler))
        app.add_handler(CommandHandler("settings", settings_handler))
        app.add_handler(CommandHandler("set_humidity_min", set_humidity_min_handler))
        app.add_handler(CommandHandler("set_humidity_max", set_humidity_max_handler))

        logger.info("Bot initialized successfully")

        # Start bot
        await app.initialize()
        await app.start()
        logger.info("Bot started successfully")

        # Start background monitoring task
        monitoring_task = asyncio.create_task(
            monitoring_loop(
                serial_reader_module.serial_reader_service,
                alert_manager_module.alert_manager,
                user_settings_module.user_settings_service,
                app.bot,
            )
        )

        # Run until stopped
        await app.updater.start_polling()

        # Keep running
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
    finally:
        # Cleanup
        if "monitoring_task" in locals():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        if "app" in locals():
            await app.stop()
            await app.shutdown()
        if serial_reader_module.serial_reader_service:
            await serial_reader_module.serial_reader_service.disconnect()
        await database.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
