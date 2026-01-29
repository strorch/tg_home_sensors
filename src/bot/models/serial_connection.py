"""SerialConnection data model."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class SerialConnection(BaseModel):
    """Represents Arduino serial connection configuration and state.
    
    Attributes:
        port: Serial port path (e.g., "/dev/ttyUSB0", "COM3").
        baud_rate: Baud rate for communication.
        timeout: Read timeout in seconds.
        is_connected: Current connection status.
        last_successful_read: Timestamp of last successful data read.
        reconnect_attempts: Number of consecutive reconnection attempts.
        backoff_delay: Current backoff delay for reconnection (seconds).
    """
    
    port: str = Field(min_length=1)
    baud_rate: Literal[9600, 19200, 38400, 57600, 115200] = 9600
    timeout: float = Field(default=2.0, gt=0)
    is_connected: bool = False
    last_successful_read: Optional[datetime] = None
    reconnect_attempts: int = Field(default=0, ge=0)
    backoff_delay: float = Field(default=1.0, ge=1.0, le=60.0)
    
    def calculate_backoff(self) -> float:
        """Calculate exponential backoff delay.
        
        Returns:
            Backoff delay in seconds (1.0 to 60.0).
        """
        delay = min(2 ** self.reconnect_attempts, 60.0)
        return max(delay, 1.0)
    
    def reset_backoff(self) -> None:
        """Reset backoff on successful connection."""
        self.reconnect_attempts = 0
        self.backoff_delay = 1.0
        self.is_connected = True
    
    def increment_backoff(self) -> None:
        """Increment backoff on failed connection."""
        self.reconnect_attempts += 1
        self.backoff_delay = self.calculate_backoff()
        self.is_connected = False
