# src/services/group-task-service.py
"""Business logic for group task management."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import TaskNotFoundError, ValidationError
from src.database.models.task import Task, TaskStatus, TaskPriority

TIMEZONE = ZoneInfo(settings.TIMEZONE)


class GroupTaskService:
    """Business logic for group task operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_group_task(
        self,
        group_id: int,
        title: str,
        assignee_id: int,
        assigned_by_id: int,
        description: str | None = None,
        due_date: datetime | None = None,
        reminder_interval_minutes: int | None = None,
    ) -> Task:
        """Create a new group task.

        Args:
            group_id: Telegram group/chat ID
            title: Task title
            assignee_id: User ID assigned to task
            assigned_by_id: Admin user ID who created task
            description: Optional task description
            due_date: Optional deadline
            reminder_interval_minutes: Recurring reminder interval
        """
        # Validate title
        title = title.strip()
        if not title:
            raise ValidationError("title", "Title cannot be empty")
        if len(title) > 255:
            raise ValidationError("title", "Title too long (max 255 chars)")

        # Validate reminder interval
        if reminder_interval_minutes is not None:
            if reminder_interval_minutes < settings.MIN_REMINDER_INTERVAL:
                raise ValidationError(
                    "reminder_interval_minutes",
                    f"Minimum interval is {settings.MIN_REMINDER_INTERVAL} minutes"
                )

        task = Task(
            user_id=assignee_id,  # Owner is assignee
            group_id=group_id,
            assignee_id=assignee_id,
            assigned_by_id=assigned_by_id,
            title=title,
            description=description,
            due_date=due_date,
            reminder_interval_minutes=reminder_interval_minutes,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_group_tasks(
        self, group_id: int, status: TaskStatus | None = None
    ) -> list[Task]:
        """Get all tasks for a group, optionally filtered by status."""
        query = select(Task).where(Task.group_id == group_id)
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_user_tasks(self, user_id: int, group_id: int | None = None) -> list[Task]:
        """Get tasks assigned to a user.

        Args:
            user_id: User ID
            group_id: Optional - filter by specific group
        """
        query = select(Task).where(Task.assignee_id == user_id)
        if group_id:
            query = query.where(Task.group_id == group_id)
        # Only active tasks (not completed/cancelled)
        query = query.where(
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.SUBMITTED])
        )
        query = query.order_by(Task.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_task_by_id(self, task_id: int, group_id: int | None = None) -> Task | None:
        """Get task by ID, optionally verify group ownership."""
        query = select(Task).where(Task.id == task_id)
        if group_id:
            query = query.where(Task.group_id == group_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def submit_task(self, task_id: int, user_id: int) -> Task:
        """Assignee submits task for admin verification.

        Args:
            task_id: Task ID
            user_id: Must be the assignee
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if task.assignee_id != user_id:
            raise ValidationError("user_id", "Only assignee can submit task")

        if task.status not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            raise ValidationError(
                "status",
                f"Cannot submit task with status {task.status.value}"
            )

        task.status = TaskStatus.SUBMITTED
        task.submitted_at = datetime.now(TIMEZONE)
        await self.session.flush()
        return task

    async def verify_task(self, task_id: int, admin_id: int) -> Task:
        """Admin verifies and completes task.

        Args:
            task_id: Task ID
            admin_id: Admin user ID performing verification
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if task.status != TaskStatus.SUBMITTED:
            raise ValidationError(
                "status",
                "Can only verify submitted tasks"
            )

        task.status = TaskStatus.COMPLETED
        task.verified_at = datetime.now(TIMEZONE)
        task.verified_by_id = admin_id
        # Clear reminders
        task.reminder_interval_minutes = None
        task.last_reminder_sent = None
        await self.session.flush()
        return task

    async def reject_task(self, task_id: int, admin_id: int) -> Task:
        """Admin rejects submission, task goes back to IN_PROGRESS.

        Args:
            task_id: Task ID
            admin_id: Admin user ID performing rejection
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if task.status != TaskStatus.SUBMITTED:
            raise ValidationError(
                "status",
                "Can only reject submitted tasks"
            )

        task.status = TaskStatus.IN_PROGRESS
        task.submitted_at = None
        await self.session.flush()
        return task

    async def reassign_task(
        self, task_id: int, new_assignee_id: int, admin_id: int
    ) -> Task:
        """Reassign task to different user.

        Args:
            task_id: Task ID
            new_assignee_id: New user to assign
            admin_id: Admin performing reassignment
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            raise ValidationError(
                "status",
                "Cannot reassign completed/cancelled tasks"
            )

        task.assignee_id = new_assignee_id
        task.user_id = new_assignee_id  # Update owner too
        task.status = TaskStatus.PENDING  # Reset status
        task.submitted_at = None
        await self.session.flush()
        return task

    async def update_reminder_interval(
        self, task_id: int, interval_minutes: int
    ) -> Task:
        """Update reminder interval for a task."""
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if interval_minutes < settings.MIN_REMINDER_INTERVAL:
            raise ValidationError(
                "interval_minutes",
                f"Minimum interval is {settings.MIN_REMINDER_INTERVAL} minutes"
            )

        task.reminder_interval_minutes = interval_minutes
        await self.session.flush()
        return task

    async def update_task(
        self,
        task_id: int,
        title: str | None = None,
        due_date: datetime | None = None
    ) -> Task:
        """Update task title and/or deadline (admin only).

        Per plan: /edit allows title + deadline only.
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        if title is not None:
            title = title.strip()
            if not title:
                raise ValidationError("title", "Title cannot be empty")
            if len(title) > 255:
                raise ValidationError("title", "Title too long (max 255 chars)")
            task.title = title

        if due_date is not None:
            task.due_date = due_date

        await self.session.flush()
        return task

    async def get_tasks_needing_reminder(self) -> list[Task]:
        """Get group tasks that need reminder sent.

        Criteria:
        - Has group_id (is group task)
        - Has reminder_interval_minutes set
        - Status is PENDING or IN_PROGRESS
        - Either never reminded, or last_reminder_sent + interval has passed
        """
        now = datetime.now(TIMEZONE)
        query = select(Task).where(
            Task.group_id.isnot(None),
            Task.reminder_interval_minutes.isnot(None),
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
        result = await self.session.execute(query)
        tasks = list(result.scalars().all())

        # Filter by interval
        due_tasks = []
        for task in tasks:
            if task.last_reminder_sent is None:
                due_tasks.append(task)
            else:
                next_reminder = task.last_reminder_sent + timedelta(
                    minutes=task.reminder_interval_minutes
                )
                if now >= next_reminder:
                    due_tasks.append(task)

        return due_tasks

    async def mark_reminder_sent(self, task_id: int) -> None:
        """Update last_reminder_sent timestamp."""
        task = await self.get_task_by_id(task_id)
        if task:
            task.last_reminder_sent = datetime.now(TIMEZONE)
            await self.session.flush()
