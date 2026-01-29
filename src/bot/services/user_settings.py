"""User settings service for database operations."""
import logging
from datetime import datetime, timezone
from typing import Optional

from src.bot.models.user import User
from src.bot.models.alert_state import AlertState
from src.bot.services.database import Database


logger = logging.getLogger(__name__)


class UserSettingsService:
    """Service for managing user settings and alert states."""
    
    def __init__(self, database: Database) -> None:
        """Initialize user settings service.
        
        Args:
            database: Database instance.
        """
        self.db = database
    
    async def get_user(self, chat_id: int) -> Optional[User]:
        """Get user by chat ID.
        
        Args:
            chat_id: Telegram chat ID.
            
        Returns:
            User object if found, None otherwise.
        """
        try:
            async with self.db.connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM users WHERE chat_id = ?",
                    (chat_id,)
                )
                row = await cursor.fetchone()
                
                if row is None:
                    return None
                
                return User(
                    chat_id=row["chat_id"],
                    humidity_min=row["humidity_min"],
                    humidity_max=row["humidity_max"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"])
                )
        except Exception as e:
            logger.error(f"Error getting user {chat_id}: {e}")
            raise
    
    async def create_user(
        self,
        chat_id: int,
        humidity_min: float = 40.0,
        humidity_max: float = 60.0
    ) -> User:
        """Create a new user with default settings.
        
        Args:
            chat_id: Telegram chat ID.
            humidity_min: Minimum humidity threshold.
            humidity_max: Maximum humidity threshold.
            
        Returns:
            Created User object.
        """
        now = datetime.now(timezone.utc)
        
        try:
            user = User(
                chat_id=chat_id,
                humidity_min=humidity_min,
                humidity_max=humidity_max,
                created_at=now,
                updated_at=now
            )
            
            async with self.db.connection.cursor() as cursor:
                await cursor.execute(
                    """INSERT INTO users (chat_id, humidity_min, humidity_max, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user.chat_id, user.humidity_min, user.humidity_max,
                     user.created_at.isoformat(), user.updated_at.isoformat())
                )
                
                # Create alert state
                await cursor.execute(
                    """INSERT INTO alert_states (chat_id, current_state)
                       VALUES (?, 'normal')""",
                    (chat_id,)
                )
                
                await self.db.connection.commit()
            
            logger.info(f"Created user {chat_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {chat_id}: {e}")
            raise
    
    async def update_user_settings(
        self,
        chat_id: int,
        humidity_min: Optional[float] = None,
        humidity_max: Optional[float] = None
    ) -> User:
        """Update user humidity settings.
        
        Args:
            chat_id: Telegram chat ID.
            humidity_min: New minimum threshold (if provided).
            humidity_max: New maximum threshold (if provided).
            
        Returns:
            Updated User object.
        """
        user = await self.get_user(chat_id)
        if user is None:
            raise ValueError(f"User {chat_id} not found")
        
        # Update fields
        if humidity_min is not None:
            user.humidity_min = humidity_min
        if humidity_max is not None:
            user.humidity_max = humidity_max
        user.updated_at = datetime.now(timezone.utc)
        
        # Validate
        if user.humidity_max <= user.humidity_min:
            raise ValueError("humidity_max must be greater than humidity_min")
        
        try:
            async with self.db.connection.cursor() as cursor:
                await cursor.execute(
                    """UPDATE users 
                       SET humidity_min = ?, humidity_max = ?, updated_at = ?
                       WHERE chat_id = ?""",
                    (user.humidity_min, user.humidity_max, 
                     user.updated_at.isoformat(), chat_id)
                )
                await self.db.connection.commit()
            
            logger.info(f"Updated settings for user {chat_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error updating user {chat_id}: {e}")
            raise
    
    async def get_alert_state(self, chat_id: int) -> Optional[AlertState]:
        """Get alert state for user.
        
        Args:
            chat_id: Telegram chat ID.
            
        Returns:
            AlertState object if found, None otherwise.
        """
        try:
            async with self.db.connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM alert_states WHERE chat_id = ?",
                    (chat_id,)
                )
                row = await cursor.fetchone()
                
                if row is None:
                    return None
                
                return AlertState(
                    chat_id=row["chat_id"],
                    current_state=row["current_state"],
                    last_alert_time=(datetime.fromisoformat(row["last_alert_time"])
                                    if row["last_alert_time"] else None),
                    last_alert_type=row["last_alert_type"]
                )
        except Exception as e:
            logger.error(f"Error getting alert state for user {chat_id}: {e}")
            raise


# Global user settings service instance (initialized in main.py)
user_settings_service: Optional[UserSettingsService] = None
