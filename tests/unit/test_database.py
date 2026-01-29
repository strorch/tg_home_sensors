"""Unit tests for database initialization."""
import pytest
import aiosqlite
from pathlib import Path
from src.bot.services.database import Database


@pytest.mark.asyncio
async def test_database_creates_directory(tmp_path: Path) -> None:
    """Test that database creates parent directory if it doesn't exist."""
    db_path = tmp_path / "data" / "test.db"
    assert not db_path.parent.exists()
    
    db = Database(str(db_path))
    await db.connect()
    
    assert db_path.parent.exists()
    assert db_path.exists()
    
    await db.close()


@pytest.mark.asyncio
async def test_database_schema_creation(tmp_path: Path) -> None:
    """Test that database creates required tables."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.connect()
    
    # Check users table exists
    async with db.connection.cursor() as cursor:
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == "users"
    
    # Check alert_states table exists
    async with db.connection.cursor() as cursor:
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alert_states'"
        )
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == "alert_states"
    
    await db.close()


@pytest.mark.asyncio
async def test_database_connection_property(tmp_path: Path) -> None:
    """Test that connection property raises error when not connected."""
    db = Database(str(tmp_path / "test.db"))
    
    with pytest.raises(RuntimeError, match="Database not connected"):
        _ = db.connection


@pytest.mark.asyncio
async def test_database_close(tmp_path: Path) -> None:
    """Test that database can be closed."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.connect()
    
    assert db._connection is not None
    
    await db.close()
    
    assert db._connection is None


@pytest.mark.asyncio
async def test_database_users_table_schema(tmp_path: Path) -> None:
    """Test users table has correct columns and constraints."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.connect()
    
    async with db.connection.cursor() as cursor:
        await cursor.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
    
    column_names = [col[1] for col in columns]
    assert "chat_id" in column_names
    assert "humidity_min" in column_names
    assert "humidity_max" in column_names
    assert "created_at" in column_names
    assert "updated_at" in column_names
    
    await db.close()


@pytest.mark.asyncio
async def test_database_alert_states_table_schema(tmp_path: Path) -> None:
    """Test alert_states table has correct columns."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.connect()
    
    async with db.connection.cursor() as cursor:
        await cursor.execute("PRAGMA table_info(alert_states)")
        columns = await cursor.fetchall()
    
    column_names = [col[1] for col in columns]
    assert "chat_id" in column_names
    assert "current_state" in column_names
    assert "last_alert_time" in column_names
    assert "last_alert_type" in column_names
    
    await db.close()
