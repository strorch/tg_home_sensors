"""User data model."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from pydantic import ValidationInfo


class User(BaseModel):
    """Represents a Telegram user with personalized alert thresholds.

    Attributes:
        chat_id: Telegram chat ID (primary key).
        humidity_min: Minimum acceptable humidity threshold (%).
        humidity_max: Maximum acceptable humidity threshold (%).
        created_at: When user first interacted with bot.
        updated_at: Last time settings were modified.
    """

    chat_id: int = Field(gt=0)
    humidity_min: float = Field(default=40.0, ge=0.0, le=100.0)
    humidity_max: float = Field(default=60.0, ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime

    @field_validator("humidity_max")
    @classmethod
    def max_greater_than_min(cls, v: float, info: ValidationInfo) -> float:
        """Ensure humidity_max is greater than humidity_min.

        Args:
            v: humidity_max value.
            info: Validation context with other field values.

        Returns:
            Validated humidity_max.

        Raises:
            ValueError: If humidity_max <= humidity_min.
        """
        if "humidity_min" in info.data and v <= info.data["humidity_min"]:
            raise ValueError("humidity_max must be greater than humidity_min")
        return v
