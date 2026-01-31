"""Unit tests for user settings service."""

import os
import pytest
from src.bot.services.database import Database
from src.bot.services.user_settings import UserSettingsService


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set for PostgreSQL tests")
    return url


async def _setup_database():
    db = Database(_database_url())
    await db.connect()
    await db.execute("DELETE FROM alert_states")
    await db.execute("DELETE FROM users")
    return db


@pytest.mark.asyncio
async def test_update_threshold_validates_min_less_than_max(tmp_path):
    """Test that updating thresholds validates min < max constraint."""
    database = await _setup_database()
    user_service = UserSettingsService(database)

    # Create user
    await user_service.create_or_update_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    # Try to set min >= max (should fail)
    with pytest.raises(ValueError, match="min.*less than.*max"):
        await user_service.update_user_threshold(
            chat_id=12345,
            humidity_min=65.0,  # Greater than max
            humidity_max=60.0,
        )

    # Verify user unchanged
    user = await user_service.get_user(12345)
    assert user.humidity_min == 40.0

    await database.close()


@pytest.mark.asyncio
async def test_update_threshold_validates_range_0_100(tmp_path):
    """Test that threshold values must be between 0 and 100."""
    database = await _setup_database()
    user_service = UserSettingsService(database)

    await user_service.create_or_update_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    # Try to set value < 0
    with pytest.raises(ValueError, match="0.*100"):
        await user_service.update_user_threshold(
            chat_id=12345, humidity_min=-10.0, humidity_max=60.0
        )

    # Try to set value > 100
    with pytest.raises(ValueError, match="0.*100"):
        await user_service.update_user_threshold(
            chat_id=12345, humidity_min=40.0, humidity_max=150.0
        )

    await database.close()


@pytest.mark.asyncio
async def test_update_threshold_accepts_valid_values(tmp_path):
    """Test that valid threshold updates succeed."""
    database = await _setup_database()
    user_service = UserSettingsService(database)

    await user_service.create_or_update_user(chat_id=12345, humidity_min=40.0, humidity_max=60.0)

    # Update to valid values
    await user_service.update_user_threshold(chat_id=12345, humidity_min=30.0, humidity_max=70.0)

    # Verify updated
    user = await user_service.get_user(12345)
    assert user.humidity_min == 30.0
    assert user.humidity_max == 70.0

    await database.close()
