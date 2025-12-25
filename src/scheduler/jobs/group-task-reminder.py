# src/scheduler/jobs/group-task-reminder.py
"""Scheduler jobs for group task reminders."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from loguru import logger
from sqlalchemy import select, and_

from src.core.config import settings
from src.database.models.task import Task, TaskStatus

# Import working hours from services
import importlib

TIMEZONE = ZoneInfo(settings.TIMEZONE)

# Bot and session factory injected at startup
_bot = None
_session_factory = None


def set_bot_instance(bot, session_factory):
    """Set bot instance for jobs (called during app startup)."""
    global _bot, _session_factory
    _bot = bot
    _session_factory = session_factory


def _get_working_hours():
    """Lazy import working hours module."""
    return importlib.import_module("src.services.working-hours")


async def process_group_reminders():
    """
    Runs every 5 minutes.
    Send recurring reminders for active group tasks during working hours.
    """
    wh = _get_working_hours()
    if not wh.is_working_time():
        return  # Skip outside working hours

    if not _bot or not _session_factory:
        logger.error("Bot or session not configured for group reminder jobs")
        return

    now = datetime.now(TIMEZONE)

    async with _session_factory() as session:
        # Find tasks that need reminder
        query = select(Task).where(
            and_(
                Task.group_id.isnot(None),
                Task.reminder_interval_minutes.isnot(None),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
        )
        # Only tasks not past deadline
        query = query.where(
            (Task.due_date.is_(None)) | (Task.due_date > now)
        )
        result = await session.execute(query)
        tasks = list(result.scalars().all())

        sent_count = 0
        for task in tasks:
            if _should_send_reminder(task, now):
                await _send_task_reminder(task)
                task.last_reminder_sent = now
                sent_count += 1

        await session.commit()

        if sent_count > 0:
            logger.info(f"Sent {sent_count} group task reminders")


def _should_send_reminder(task: Task, now: datetime) -> bool:
    """Check if enough time elapsed since last reminder."""
    if task.last_reminder_sent is None:
        return True
    elapsed = now - task.last_reminder_sent
    return elapsed >= timedelta(minutes=task.reminder_interval_minutes)


async def _send_task_reminder(task: Task):
    """Send reminder message to group."""
    if task.due_date:
        time_left = task.due_date - datetime.now(TIMEZONE)
        time_str = f"⏱️ Time left: {format_timedelta(time_left)}"
        deadline_str = f"📅 Deadline: {task.due_date.strftime('%d/%m %H:%M')}"
    else:
        time_str = ""
        deadline_str = "📅 No deadline"

    # Use HTML mention format for Telegram
    message = f"""⏰ Task Reminder

📋 {task.title}
👤 <a href="tg://user?id={task.assignee_id}">Assignee</a>
{deadline_str}
{time_str}

Reply /done {task.id} when complete."""

    try:
        await _bot.send_message(
            chat_id=task.group_id,
            text=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send reminder for task {task.id}: {e}")


async def check_overdue_tasks():
    """
    Runs every 15 minutes during working hours.
    Mark overdue tasks and send ONE notification (then stop reminding).
    Per validation: OVERDUE reminder gửi 1 lần rồi dừng.
    """
    wh = _get_working_hours()
    if not wh.is_working_time():
        return

    if not _bot or not _session_factory:
        return

    now = datetime.now(TIMEZONE)

    async with _session_factory() as session:
        # Find tasks past deadline that aren't already OVERDUE
        query = select(Task).where(
            and_(
                Task.group_id.isnot(None),
                Task.due_date < now,
                Task.due_date.isnot(None),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
        )
        result = await session.execute(query)
        tasks = list(result.scalars().all())

        for task in tasks:
            task.status = TaskStatus.OVERDUE
            # Clear reminders - no more notifications after this one
            task.reminder_interval_minutes = None
            await _send_overdue_notification(task, now)

        await session.commit()

        if tasks:
            logger.info(f"Marked {len(tasks)} tasks as overdue")


async def _send_overdue_notification(task: Task, now: datetime):
    """Send overdue notification to group (once only)."""
    overdue_duration = now - task.due_date

    message = f"""🚨 OVERDUE TASK

📋 {task.title}
👤 <a href="tg://user?id={task.assignee_id}">Assignee</a>
📅 Was due: {task.due_date.strftime('%d/%m %H:%M')}
⏱️ Overdue by: {format_timedelta(overdue_duration)}

<a href="tg://user?id={task.assigned_by_id}">Admin</a> please review."""

    try:
        await _bot.send_message(
            chat_id=task.group_id,
            text=message,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send overdue notification for task {task.id}: {e}")


async def cleanup_old_tasks():
    """
    Runs daily at 00:00.
    Delete tasks completed > 30 days ago.
    """
    if not _session_factory:
        return

    cutoff = datetime.now(TIMEZONE) - timedelta(
        days=settings.COMPLETED_TASK_RETENTION_DAYS
    )

    async with _session_factory() as session:
        query = select(Task).where(
            and_(
                Task.status == TaskStatus.COMPLETED,
                Task.verified_at.isnot(None),
                Task.verified_at < cutoff,
            )
        )
        result = await session.execute(query)
        old_tasks = list(result.scalars().all())

        for task in old_tasks:
            await session.delete(task)

        await session.commit()

        if old_tasks:
            logger.info(f"Cleaned up {len(old_tasks)} old completed tasks")


def format_timedelta(td: timedelta) -> str:
    """Format timedelta to human readable string."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        total_seconds = abs(total_seconds)

    total_minutes = total_seconds // 60
    hours, minutes = divmod(total_minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)
