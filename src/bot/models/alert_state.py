"""AlertState data model."""

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class AlertState(BaseModel):
    """Tracks alert status for a user to manage notifications and cooldowns.

    Attributes:
        chat_id: Telegram chat ID (foreign key to User).
        current_state: Current alert status.
        last_alert_time: Timestamp of last alert sent (None if never alerted).
        last_alert_type: Type of last alert sent.
    """

    chat_id: int = Field(gt=0)
    current_state: Literal["normal", "high_humidity", "low_humidity"] = "normal"
    last_alert_time: Optional[datetime] = None
    last_alert_type: Optional[Literal["high", "low"]] = None

    def should_send_alert(
        self,
        new_state: Literal["normal", "high_humidity", "low_humidity"],
        cooldown_seconds: int = 300,
    ) -> bool:
        """Determine if an alert should be sent based on state and cooldown.

        Args:
            new_state: The new state to transition to.
            cooldown_seconds: Minimum seconds between alerts (default: 300).

        Returns:
            True if alert should be sent, False otherwise.
        """
        # State changed - always send
        if new_state != self.current_state:
            return True

        # State unchanged but in alert state
        if new_state != "normal":
            if self.last_alert_time is None:
                return True

            # Check if cooldown expired
            elapsed = (datetime.now(timezone.utc) - self.last_alert_time).total_seconds()
            return elapsed >= cooldown_seconds

        return False
