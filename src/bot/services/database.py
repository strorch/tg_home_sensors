"""Database initialization and schema management."""

import aiosqlite
from pathlib import Path


class Database:
    """SQLite database manager with async support."""

    def __init__(self, db_path: str) -> None:
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Connect to database and initialize schema."""
        # Create parent directory if it doesn't exist
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Initialize schema
        await self._init_schema()

    async def _init_schema(self) -> None:
        """Create database tables if they don't exist."""
        if self._connection is None:
            raise RuntimeError("Database not connected")

        async with self._connection.cursor() as cursor:
            # Create users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    humidity_min REAL NOT NULL DEFAULT 40.0,
                    humidity_max REAL NOT NULL DEFAULT 60.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    CHECK (humidity_min >= 0.0 AND humidity_min <= 100.0),
                    CHECK (humidity_max >= 0.0 AND humidity_max <= 100.0),
                    CHECK (humidity_min < humidity_max)
                )
            """)

            # Create alert_states table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_states (
                    chat_id INTEGER PRIMARY KEY,
                    current_state TEXT NOT NULL DEFAULT 'normal',
                    last_alert_time TEXT,
                    last_alert_type TEXT,
                    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE,
                    CHECK (current_state IN ('normal', 'high_humidity', 'low_humidity')),
                    CHECK (last_alert_type IN ('high', 'low') OR last_alert_type IS NULL)
                )
            """)

            await self._connection.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get database connection.

        Returns:
            Active database connection.

        Raises:
            RuntimeError: If database is not connected.
        """
        if self._connection is None:
            raise RuntimeError("Database not connected")
        return self._connection
