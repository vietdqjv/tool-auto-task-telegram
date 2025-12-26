# src/bot/middlewares/group-rate-limit.py
"""Group-level rate limiting middleware."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from src.core.config import settings


class GroupRateLimitMiddleware(BaseMiddleware):
    """Rate limit requests per group (not per user)."""

    def __init__(self, max_per_minute: int = 30):
        self.cache: TTLCache = TTLCache(maxsize=1000, ttl=60)
        self.max_per_minute = max_per_minute
        self.admin_ids = set(settings.ADMIN_IDS)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Skip non-Message events
        if not isinstance(event, Message):
            return await handler(event, data)

        # Skip private chats
        if event.chat.type not in ["group", "supergroup"]:
            return await handler(event, data)

        # Admin bypass
        user_id = event.from_user.id if event.from_user else 0
        if user_id in self.admin_ids:
            return await handler(event, data)

        # Group rate limiting
        group_id = event.chat.id
        key = f"grp_{group_id}"
        count = self.cache.get(key, 0)

        if count >= self.max_per_minute:
            await event.reply(
                "Nhom dang qua tai. Thu lai sau 1 phut.",
                parse_mode=None
            )
            return  # Block handler

        self.cache[key] = count + 1
        return await handler(event, data)
