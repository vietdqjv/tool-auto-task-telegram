# src/bot/middlewares/rate-limit.py
"""Rate limiting middleware using cachetools."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from src.core.config import settings
from src.core.constants import MSG_RATE_LIMITED


class RateLimitMiddleware(BaseMiddleware):
    """Middleware to limit request rate per user."""

    def __init__(self):
        self.cache = TTLCache(maxsize=10_000, ttl=settings.RATE_LIMIT_PERIOD)
        self.limit = settings.RATE_LIMIT_REQUESTS
        self.admin_ids = set(settings.ADMIN_IDS)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0
        # Bypass rate limit for admins
        if user_id in self.admin_ids:
            return await handler(event, data)
        current = self.cache.get(user_id, 0)
        if current >= self.limit:
            return await event.answer(MSG_RATE_LIMITED)
        self.cache[user_id] = current + 1
        return await handler(event, data)
