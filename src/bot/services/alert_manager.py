"""Alert manager service for monitoring thresholds and sending alerts."""

import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from telegram import Bot

from src.bot.models.sensor_reading import SensorReading
from src.bot.models.user import User
from src.bot.models.alert_state import AlertState
from src.bot.services.database import Database


logger = logging.getLogger(__name__)


class AlertManager:
    """Service to monitor sensor readings and send threshold alerts."""

    def __init__(self, database: Database, bot: Bot) -> None:
        """Initialize alert manager.

        Args:
            database: Database instance.
            bot: Telegram Bot instance.
        """
        self.db = database
        self.bot = bot
        self.cooldown_seconds = 300  # 5 minutes

    def determine_state(
        self, reading: SensorReading, user: User
    ) -> Literal["normal", "high_humidity", "low_humidity"]:
        """Determine alert state based on reading and user thresholds.

        Args:
            reading: Current sensor reading.
            user: User with threshold settings.

        Returns:
            Current alert state.
        """
        if reading.humidity > user.humidity_max:
            return "high_humidity"
        elif reading.humidity < user.humidity_min:
            return "low_humidity"
        else:
            return "normal"

    async def check_threshold(
        self, reading: SensorReading, user: User, alert_state: AlertState
    ) -> bool:
        """Check if an alert should be sent.

        Args:
            reading: Current sensor reading.
            user: User with threshold settings.
            alert_state: Current alert state.

        Returns:
            True if alert should be sent, False otherwise.
        """
        new_state = self.determine_state(reading, user)
        return alert_state.should_send_alert(new_state, self.cooldown_seconds)

    def format_high_humidity_alert(self, reading: SensorReading, user: User) -> str:
        """Format high humidity alert message.

        Args:
            reading: Current sensor reading.
            user: User with threshold settings.

        Returns:
            Formatted alert message.
        """
        return (
            "⚠️ HIGH HUMIDITY ALERT\n\n"
            f"Current humidity: {reading.humidity:.2f}%\n"
            f"Your threshold: ≤ {user.humidity_max}%\n\n"
            "🌡️ Other readings:\n"
            f"• DHT Temp: {reading.dht_temperature:.2f}°C\n"
            f"• LM35 Temp: {reading.lm35_temperature:.2f}°C\n"
            f"• Thermistor: {reading.thermistor_temperature:.2f}°C\n\n"
            f"📅 {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            "Consider ventilating the area or using a dehumidifier."
        )

    def format_low_humidity_alert(self, reading: SensorReading, user: User) -> str:
        """Format low humidity alert message.

        Args:
            reading: Current sensor reading.
            user: User with threshold settings.

        Returns:
            Formatted alert message.
        """
        return (
            "⚠️ LOW HUMIDITY ALERT\n\n"
            f"Current humidity: {reading.humidity:.2f}%\n"
            f"Your threshold: ≥ {user.humidity_min}%\n\n"
            "🌡️ Other readings:\n"
            f"• DHT Temp: {reading.dht_temperature:.2f}°C\n"
            f"• LM35 Temp: {reading.lm35_temperature:.2f}°C\n"
            f"• Thermistor: {reading.thermistor_temperature:.2f}°C\n\n"
            f"📅 {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            "Consider using a humidifier to increase moisture levels."
        )

    def format_recovery_notification(self, reading: SensorReading, user: User) -> str:
        """Format recovery notification message.

        Args:
            reading: Current sensor reading.
            user: User with threshold settings.

        Returns:
            Formatted recovery message.
        """
        return (
            "✅ HUMIDITY BACK TO NORMAL\n\n"
            f"Current humidity: {reading.humidity:.2f}%\n"
            f"Your range: {user.humidity_min}% - {user.humidity_max}%\n\n"
            "🌡️ Current readings:\n"
            f"• DHT Temp: {reading.dht_temperature:.2f}°C\n"
            f"• LM35 Temp: {reading.lm35_temperature:.2f}°C\n"
            f"• Thermistor: {reading.thermistor_temperature:.2f}°C\n\n"
            f"📅 {reading.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            "Environment is back to acceptable levels."
        )

    async def update_alert_state(
        self,
        chat_id: int,
        new_state: Literal["normal", "high_humidity", "low_humidity"],
        alert_type: Optional[Literal["high", "low"]] = None,
    ) -> None:
        """Update alert state in database.

        Args:
            chat_id: User's chat ID.
            new_state: New alert state.
            alert_type: Type of alert sent (None for recovery).
        """
        now = datetime.now(timezone.utc)

        try:
            async with self.db.connection.cursor() as cursor:
                if new_state == "normal":
                    # Recovery - clear alert time and type
                    await cursor.execute(
                        """UPDATE alert_states 
                           SET current_state = ?, last_alert_time = NULL, last_alert_type = NULL
                           WHERE chat_id = ?""",
                        (new_state, chat_id),
                    )
                else:
                    # Alert - update state, time, and type
                    await cursor.execute(
                        """UPDATE alert_states 
                           SET current_state = ?, last_alert_time = ?, last_alert_type = ?
                           WHERE chat_id = ?""",
                        (new_state, now.isoformat(), alert_type, chat_id),
                    )

                await self.db.connection.commit()
                logger.info(f"Updated alert state for user {chat_id}: {new_state}")

        except Exception as e:
            logger.error(f"Error updating alert state for user {chat_id}: {e}")
            raise

    async def process_reading(self, reading: SensorReading, chat_id: int) -> None:
        """Process sensor reading and send alerts if needed.

        Args:
            reading: Current sensor reading.
            chat_id: User's chat ID.
        """
        try:
            # Get user settings
            async with self.db.connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
                user_row = await cursor.fetchone()

                if user_row is None:
                    return  # User not registered

                user = User(
                    chat_id=user_row["chat_id"],
                    humidity_min=user_row["humidity_min"],
                    humidity_max=user_row["humidity_max"],
                    created_at=datetime.fromisoformat(user_row["created_at"]),
                    updated_at=datetime.fromisoformat(user_row["updated_at"]),
                )

                # Get alert state
                await cursor.execute("SELECT * FROM alert_states WHERE chat_id = ?", (chat_id,))
                state_row = await cursor.fetchone()

                if state_row is None:
                    return  # No alert state

                alert_state = AlertState(
                    chat_id=state_row["chat_id"],
                    current_state=state_row["current_state"],
                    last_alert_time=(
                        datetime.fromisoformat(state_row["last_alert_time"])
                        if state_row["last_alert_time"]
                        else None
                    ),
                    last_alert_type=state_row["last_alert_type"],
                )

            # Determine new state
            new_state = self.determine_state(reading, user)

            # Check if alert should be sent
            should_alert = alert_state.should_send_alert(new_state, self.cooldown_seconds)

            if should_alert:
                # Format and send appropriate message
                if new_state == "high_humidity":
                    message = self.format_high_humidity_alert(reading, user)
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    await self.update_alert_state(chat_id, new_state, "high")
                    logger.info(f"Sent high humidity alert to user {chat_id}")

                elif new_state == "low_humidity":
                    message = self.format_low_humidity_alert(reading, user)
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    await self.update_alert_state(chat_id, new_state, "low")
                    logger.info(f"Sent low humidity alert to user {chat_id}")

                elif new_state == "normal" and alert_state.current_state != "normal":
                    # Recovery notification
                    message = self.format_recovery_notification(reading, user)
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    await self.update_alert_state(chat_id, new_state, None)
                    logger.info(f"Sent recovery notification to user {chat_id}")

        except Exception as e:
            logger.error(f"Error processing reading for user {chat_id}: {e}", exc_info=True)


# Global alert manager instance (initialized in main.py)
alert_manager: Optional[AlertManager] = None
