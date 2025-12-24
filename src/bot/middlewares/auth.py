# src/bot/middlewares/auth.py
"""Authentication middleware - registers users on first message."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.database import async_session_factory, UserRepository


class AuthMiddleware(BaseMiddleware):
    """Middleware to ensure user exists in database."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        if not user:
            return await handler(event, data)

        async with async_session_factory() as session:
            repo = UserRepository(session)
            db_user, created = await repo.get_or_create(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code or "en"
            )
            await session.commit()
            data["db_user"] = db_user

        return await handler(event, data)
