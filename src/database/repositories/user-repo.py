# src/database/repositories/user-repo.py
"""User repository for database operations."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User


class UserRepository:
    """Repository for User CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by Telegram ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None = None,
        language_code: str = "en"
    ) -> tuple[User, bool]:
        """Get existing user or create new one. Returns (user, created)."""
        user = await self.get_by_id(user_id)
        if user:
            # Update user info if changed
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            return user, False

        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code
        )
        self.session.add(user)
        await self.session.flush()
        return user, True

    async def update(self, user: User) -> User:
        """Update user."""
        await self.session.flush()
        return user

    async def set_admin(self, user_id: int, is_admin: bool = True) -> User | None:
        """Set user admin status."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_admin = is_admin
            await self.session.flush()
        return user
