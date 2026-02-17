"""MCP server and tool definitions for sensor access."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, AsyncIterator, Awaitable, Callable, Literal, cast

from mcp.server.fastmcp import FastMCP

from src.bot.models.sensor_reading import SensorReading
from src.bot.models.user import User
from src.bot.services.database import Database
from src.bot.services.sensor_history import SensorHistoryService
from src.bot.services.user_settings import UserSettingsService
from src.config import Config
from src.mcp.auth import ApiKeyTokenVerifier, build_auth_settings


logger = logging.getLogger(__name__)
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SensorMCPToolService:
    """Business logic behind MCP tools."""

    def __init__(
        self,
        user_settings_service: UserSettingsService,
        sensor_history_service: SensorHistoryService,
        stale_after_seconds: int = 10,
    ) -> None:
        self.user_settings_service = user_settings_service
        self.sensor_history_service = sensor_history_service
        self.stale_after_seconds = stale_after_seconds

    async def get_current_reading(self, chat_id: int) -> dict[str, Any]:
        """Return latest reading plus freshness metadata for a user."""
        user = await self._require_user(chat_id)
        reading = await self.sensor_history_service.get_latest()

        if reading is None:
            return {
                "status": "no_data",
                "chat_id": chat_id,
                "thresholds": self._serialize_thresholds(user),
                "reading": None,
                "age_seconds": None,
                "is_stale": True,
            }

        now = datetime.now(timezone.utc)
        age_seconds = max(0, int((now - reading.timestamp).total_seconds()))
        is_stale = age_seconds > self.stale_after_seconds
        status = "stale" if is_stale else "ok"

        return {
            "status": status,
            "chat_id": chat_id,
            "thresholds": self._serialize_thresholds(user),
            "reading": self._serialize_reading(reading),
            "age_seconds": age_seconds,
            "is_stale": is_stale,
        }

    async def get_recent_readings(
        self,
        chat_id: int,
        minutes: int = 60,
        limit: int = 300,
    ) -> dict[str, Any]:
        """Return recent reading window and aggregate stats."""
        if minutes <= 0 or minutes > 7 * 24 * 60:
            raise ValueError("minutes must be between 1 and 10080")
        if limit <= 0 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        user = await self._require_user(chat_id)
        readings = await self.sensor_history_service.get_recent(minutes=minutes, limit=limit)
        humidity_values = [item.humidity for item in readings]

        return {
            "status": "ok",
            "chat_id": chat_id,
            "thresholds": self._serialize_thresholds(user),
            "window_minutes": minutes,
            "limit": limit,
            "summary": {
                "count": len(readings),
                "avg_humidity": (
                    round(sum(humidity_values) / len(humidity_values), 2)
                    if humidity_values
                    else None
                ),
                "min_humidity": min(humidity_values) if humidity_values else None,
                "max_humidity": max(humidity_values) if humidity_values else None,
            },
            "readings": [self._serialize_reading(item) for item in readings],
        }

    async def set_humidity_min(self, chat_id: int, value: float) -> dict[str, Any]:
        """Set minimum humidity threshold for a user."""
        self._validate_humidity(value)
        user = await self._require_user(chat_id)
        if value >= user.humidity_max:
            raise ValueError(
                f"humidity_min must be less than current humidity_max ({user.humidity_max})"
            )

        updated = await self.user_settings_service.update_user_threshold(
            chat_id=chat_id,
            humidity_min=value,
            humidity_max=user.humidity_max,
        )
        return {
            "status": "ok",
            "chat_id": chat_id,
            "humidity_min": updated.humidity_min,
            "humidity_max": updated.humidity_max,
            "updated_at": updated.updated_at.isoformat(),
        }

    async def set_humidity_max(self, chat_id: int, value: float) -> dict[str, Any]:
        """Set maximum humidity threshold for a user."""
        self._validate_humidity(value)
        user = await self._require_user(chat_id)
        if value <= user.humidity_min:
            raise ValueError(
                f"humidity_max must be greater than current humidity_min ({user.humidity_min})"
            )

        updated = await self.user_settings_service.update_user_threshold(
            chat_id=chat_id,
            humidity_min=user.humidity_min,
            humidity_max=value,
        )
        return {
            "status": "ok",
            "chat_id": chat_id,
            "humidity_min": updated.humidity_min,
            "humidity_max": updated.humidity_max,
            "updated_at": updated.updated_at.isoformat(),
        }

    async def _require_user(self, chat_id: int) -> User:
        user = await self.user_settings_service.get_user(chat_id)
        if user is None:
            raise ValueError(f"User {chat_id} not found. Initialize with /start first.")
        return user

    @staticmethod
    def _validate_humidity(value: float) -> None:
        if value < 0 or value > 100:
            raise ValueError("Humidity threshold must be between 0 and 100")

    @staticmethod
    def _serialize_thresholds(user: User) -> dict[str, float]:
        return {
            "humidity_min": user.humidity_min,
            "humidity_max": user.humidity_max,
        }

    @staticmethod
    def _serialize_reading(reading: SensorReading) -> dict[str, Any]:
        return {
            "humidity": reading.humidity,
            "dht_temperature": reading.dht_temperature,
            "lm35_temperature": reading.lm35_temperature,
            "thermistor_temperature": reading.thermistor_temperature,
            "recorded_at": reading.timestamp.isoformat(),
        }


def create_mcp_server(config: Config) -> FastMCP:
    """Create and configure MCP server instance."""
    if not config.mcp_api_key:
        raise ValueError("MCP_API_KEY is required to run MCP server")

    database = Database(config.database_url)
    user_settings_service = UserSettingsService(database)
    sensor_history_service = SensorHistoryService(database)
    tools = SensorMCPToolService(
        user_settings_service=user_settings_service,
        sensor_history_service=sensor_history_service,
    )

    base_url = f"http://{config.mcp_host}:{config.mcp_port}"
    configured_log_level = config.log_level.upper()
    if configured_log_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        log_level: LogLevel = cast(LogLevel, configured_log_level)
    else:
        log_level = "INFO"

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        await database.connect()
        logger.info("MCP database connected")
        try:
            yield
        finally:
            await database.close()
            logger.info("MCP database closed")

    mcp = FastMCP(
        name="tg-home-sensors-mcp",
        instructions=(
            "Use tools to read home sensor data and manage humidity thresholds. "
            "Always pass explicit chat_id."
        ),
        host=config.mcp_host,
        port=config.mcp_port,
        streamable_http_path="/mcp",
        log_level=log_level,
        auth=build_auth_settings(base_url),
        token_verifier=ApiKeyTokenVerifier(config.mcp_api_key),
        lifespan=lifespan,
    )

    @mcp.tool(description="Get latest sensor reading and freshness status for a chat_id.")
    async def get_current_reading(chat_id: int) -> dict[str, Any]:
        return await _run_tool_with_logging(
            tool_name="get_current_reading",
            chat_id=chat_id,
            action=lambda: tools.get_current_reading(chat_id=chat_id),
        )

    @mcp.tool(description="Get recent sensor readings for a chat_id within a minute window.")
    async def get_recent_readings(
        chat_id: int,
        minutes: int = 60,
        limit: int = 300,
    ) -> dict[str, Any]:
        return await _run_tool_with_logging(
            tool_name="get_recent_readings",
            chat_id=chat_id,
            action=lambda: tools.get_recent_readings(chat_id=chat_id, minutes=minutes, limit=limit),
        )

    @mcp.tool(description="Update minimum humidity threshold for a chat_id.")
    async def set_humidity_min(chat_id: int, value: float) -> dict[str, Any]:
        return await _run_tool_with_logging(
            tool_name="set_humidity_min",
            chat_id=chat_id,
            action=lambda: tools.set_humidity_min(chat_id=chat_id, value=value),
        )

    @mcp.tool(description="Update maximum humidity threshold for a chat_id.")
    async def set_humidity_max(chat_id: int, value: float) -> dict[str, Any]:
        return await _run_tool_with_logging(
            tool_name="set_humidity_max",
            chat_id=chat_id,
            action=lambda: tools.set_humidity_max(chat_id=chat_id, value=value),
        )

    return mcp


async def _run_tool_with_logging(
    tool_name: str,
    chat_id: int,
    action: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    started = perf_counter()
    try:
        result = await action()
        duration_ms = int((perf_counter() - started) * 1000)
        logger.info("mcp_tool_success tool=%s chat_id=%s duration_ms=%s", tool_name, chat_id, duration_ms)
        return result
    except Exception:
        duration_ms = int((perf_counter() - started) * 1000)
        logger.exception(
            "mcp_tool_failure tool=%s chat_id=%s duration_ms=%s",
            tool_name,
            chat_id,
            duration_ms,
        )
        raise
