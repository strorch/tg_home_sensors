"""Database initialization and schema management."""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.bot.models.db import metadata

class Database:
    """PostgreSQL database manager using SQLAlchemy async engine."""

    def __init__(self, database_url: str) -> None:
        """Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL.
        """
        if not database_url:
            raise ValueError("database_url is required")

        self.database_url = database_url
        self._engine: AsyncEngine | None = None
        self._session_factory: sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Connect to database and initialize schema."""
        self._engine = create_async_engine(self.database_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )
        await self._init_schema()

    async def _init_schema(self) -> None:
        """Create database tables if they don't exist."""
        if self._engine is None:
            raise RuntimeError("Database not connected")

        async with self._engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> None:
        """Execute a statement without returning results."""
        session = self._require_session()
        async with session() as db:
            await db.execute(text(sql), params or {})
            await db.commit()

    async def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        """Fetch a single row as a dict."""
        session = self._require_session()
        async with session() as db:
            result = await db.execute(text(sql), params or {})
            row = result.mappings().first()
            return dict(row) if row is not None else None

    async def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch all rows as a list of dicts."""
        session = self._require_session()
        async with session() as db:
            result = await db.execute(text(sql), params or {})
            return [dict(row) for row in result.mappings().all()]

    async def close(self) -> None:
        """Close database connection."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def _require_session(self) -> sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("Database not connected")
        return self._session_factory
