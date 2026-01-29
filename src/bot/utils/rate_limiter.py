"""Rate limiting utilities."""
import time
from functools import wraps
from typing import Any, Callable, Dict
from telegram import Update
from telegram.ext import ContextTypes


# Rate limit state: user_id -> last_request_time
_rate_limit_state: Dict[int, float] = {}


def rate_limit(seconds: int = 3) -> Callable[..., Any]:
    """Decorator to rate limit Telegram command handlers.
    
    Args:
        seconds: Minimum seconds between requests.
        
    Returns:
        Decorated handler function.
        
    Example:
        @rate_limit(seconds=3)
        async def sensors_handler(update, context):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            user_id = update.effective_user.id if update.effective_user else 0
            current_time = time.time()
            
            # Check rate limit
            if user_id in _rate_limit_state:
                elapsed = current_time - _rate_limit_state[user_id]
                if elapsed < seconds:
                    remaining = int(seconds - elapsed) + 1
                    await update.message.reply_text(
                        f"⏸️ Please wait {remaining} more second{'s' if remaining > 1 else ''} "
                        f"before requesting again."
                    )
                    return None
            
            # Update rate limit state
            _rate_limit_state[user_id] = current_time
            
            # Call original handler
            return await func(update, context)
        
        return wrapper
    return decorator
