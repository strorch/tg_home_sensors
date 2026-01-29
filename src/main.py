"""Bot entry point."""
import asyncio
import logging
from telegram.ext import Application, CommandHandler

from src.config import load_config
from src.bot.services.database import Database
from src.bot.services.serial_reader import SerialReaderService
from src.bot.services.user_settings import UserSettingsService
from src.bot.utils.logger import setup_logging
from src.bot.handlers.start import start_handler, help_handler
from src.bot.handlers.sensors import sensors_handler, status_handler

# Import global service instances
import src.bot.services.serial_reader as serial_reader_module
import src.bot.services.user_settings as user_settings_module


logger = logging.getLogger(__name__)


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
    database = Database(config.database_path)
    try:
        await database.connect()
        logger.info(f"Database initialized at {config.database_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Initialize services
    user_settings_module.user_settings_service = UserSettingsService(database)
    serial_reader_module.serial_reader_service = SerialReaderService(
        port=config.serial_port,
        baud_rate=config.serial_baud_rate
    )
    
    # Connect to Arduino
    connected = await serial_reader_module.serial_reader_service.connect()
    if connected:
        logger.info("Arduino connected successfully")
    else:
        logger.warning("Failed to connect to Arduino - will retry in background")

    serial_reader_stop_event = asyncio.Event()
    serial_reader_task = asyncio.create_task(
        serial_reader_module.serial_reader_service.run(serial_reader_stop_event)
    )
    
    # Initialize bot application
    try:
        app = Application.builder().token(config.telegram_bot_token).build()
        
        # Register handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("sensors", sensors_handler))
        app.add_handler(CommandHandler("status", status_handler))
        
        logger.info("Bot initialized successfully")
        
        # Start bot
        await app.initialize()
        await app.start()
        logger.info("Bot started successfully")
        
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
        if 'app' in locals():
            await app.stop()
            await app.shutdown()
        if serial_reader_module.serial_reader_service:
            serial_reader_stop_event.set()
            await serial_reader_task
            await serial_reader_module.serial_reader_service.disconnect()
        await database.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
