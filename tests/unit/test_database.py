"""Unit tests for database initialization."""

import os
import pytest
from src.bot.services.database import Database


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set for PostgreSQL tests")
    return url


@pytest.mark.asyncio
async def test_database_requires_url() -> None:
    """Test that database URL is required."""
    with pytest.raises(ValueError, match="database_url is required"):
        Database("")


@pytest.mark.asyncio
async def test_database_schema_creation() -> None:
    """Test that database creates required tables."""
    db = Database(_database_url())
    await db.connect()

    users = await db.fetch_one("SELECT to_regclass('public.users') AS name")
    assert users is not None
    assert users["name"] == "users"

    alert_states = await db.fetch_one("SELECT to_regclass('public.alert_states') AS name")
    assert alert_states is not None
    assert alert_states["name"] == "alert_states"

    sensor_readings = await db.fetch_one("SELECT to_regclass('public.sensor_readings') AS name")
    assert sensor_readings is not None
    assert sensor_readings["name"] == "sensor_readings"

    await db.close()


@pytest.mark.asyncio
async def test_database_close() -> None:
    """Test that database can be closed."""
    db = Database(_database_url())
    await db.connect()
    assert db._engine is not None

    await db.close()
    assert db._engine is None
