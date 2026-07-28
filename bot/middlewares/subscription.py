from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.logger import logger


class SubscriptionMiddleware(BaseMiddleware):
    """Majburiy obuna tekshirish middleware"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        # Admin lar uchun tekshirish yo'q
        from config import ADMIN_IDS
        
        user = data.get("event_from_user")
        if not user or user.id in ADMIN_IDS:
            return await handler(event, data)

        # /start buyrug'i uchun tekshirish yo'q
        if isinstance(event, Message) and event.text == "/start":
            return await handler(event, data)

        # Subscription check_subscription callback uchun tekshirish yo'q
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        return await handler(event, data)
