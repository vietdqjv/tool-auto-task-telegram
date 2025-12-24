# src/services/notification.py
"""Notification service for sending messages via bot."""
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from src.database.models.task import Task
from src.core.constants import MSG_TASK_CREATED


class NotificationService:
    """Service for sending Telegram notifications."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_reminder(self, user_id: int, task: Task) -> bool:
        """Send task reminder to user."""
        message = f"Reminder: *{task.title}*"
        if task.description:
            message += f"\n\n{task.description}"
        return await self._send(user_id, message)

    async def send_task_created(self, user_id: int, task: Task) -> bool:
        """Send task creation confirmation."""
        due_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "Not set"
        message = MSG_TASK_CREATED.format(
            title=task.title,
            due_date=due_str,
            task_id=task.id
        )
        return await self._send(user_id, message)

    async def send_text(self, user_id: int, text: str) -> bool:
        """Send plain text message."""
        return await self._send(user_id, text)

    async def _send(self, user_id: int, text: str) -> bool:
        """Internal send with error handling."""
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown"
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to send to {user_id}: {e}")
            return False
