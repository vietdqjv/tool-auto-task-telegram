# src/scheduler/jobs/notify.py
"""Notification job definitions."""
from loguru import logger

# Note: Bot instance injected at runtime via app state
_bot = None
_session_factory = None


def set_bot_instance(bot, session_factory):
    """Set bot instance for jobs (called during app startup)."""
    global _bot, _session_factory
    _bot = bot
    _session_factory = session_factory


async def send_reminder_job(user_id: int, task_id: int):
    """Job: Send reminder for a specific task."""
    if not _bot or not _session_factory:
        logger.error("Bot or session not configured for jobs")
        return

    from src.database.repositories.task_repo import TaskRepository
    from src.services.notification import NotificationService

    async with _session_factory() as session:
        repo = TaskRepository(session)
        task = await repo.get_by_id(task_id)

        if not task:
            logger.warning(f"Task {task_id} not found for reminder")
            return

        # Clear reminder after sending
        task.reminder_at = None
        await session.commit()

        notification = NotificationService(_bot)
        success = await notification.send_reminder(user_id, task)

        if success:
            logger.info(f"Sent reminder for task {task_id} to user {user_id}")
        else:
            logger.error(f"Failed to send reminder for task {task_id}")


async def check_due_tasks_job():
    """Job: Check for tasks with passed due dates (interval job)."""
    if not _bot or not _session_factory:
        return

    from datetime import datetime, timezone
    from src.database.repositories.task_repo import TaskRepository
    from src.services.notification import NotificationService

    async with _session_factory() as session:
        repo = TaskRepository(session)
        tasks = await repo.get_due_reminders(before=datetime.now(timezone.utc))

        notification = NotificationService(_bot)
        for task in tasks:
            await notification.send_reminder(task.user_id, task)
            task.reminder_at = None

        await session.commit()

        if tasks:
            logger.info(f"Processed {len(tasks)} due reminders")
