from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from utils.logger import logger


class LoggingMiddleware(BaseMiddleware):
    """Barcha xabarlarni loglash"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        try:
            user = data.get("event_from_user")
            if user and isinstance(event, Message):
                logger.info(
                    f"User {user.id} ({user.full_name}): {event.text or '[media]'}"
                )
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Handler xatosi: {e}")
            raise
