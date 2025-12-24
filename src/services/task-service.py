# src/services/task-service.py
"""Task business logic service."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import TaskNotFoundError, ValidationError
from src.database.models.task import TaskStatus, TaskPriority


class TaskService:
    """Business logic for task operations."""

    def __init__(self, session: AsyncSession):
        # Import here to avoid circular imports with kebab-case files
        import importlib
        task_repo = importlib.import_module("src.database.repositories.task-repo")
        self.repo = task_repo.TaskRepository(session)

    async def create_task(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        due_date: datetime | None = None,
        reminder_at: datetime | None = None
    ):
        """Create a new task with validation."""
        # Validate title
        title = title.strip()
        if not title:
            raise ValidationError("title", "Title cannot be empty")
        if len(title) > 255:
            raise ValidationError("title", "Title too long (max 255 chars)")

        # Parse priority
        try:
            priority_enum = TaskPriority(priority.lower())
        except ValueError:
            priority_enum = TaskPriority.MEDIUM

        # Validate reminder
        if reminder_at and reminder_at < datetime.now(reminder_at.tzinfo):
            raise ValidationError("reminder_at", "Reminder must be in the future")

        return await self.repo.create(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority_enum,
            due_date=due_date,
            reminder_at=reminder_at
        )

    async def get_user_tasks(
        self,
        user_id: int,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10
    ):
        """Get paginated tasks for user."""
        status_enum = TaskStatus(status) if status else None
        offset = (page - 1) * page_size
        return await self.repo.get_all_by_user(
            user_id=user_id,
            status=status_enum,
            limit=page_size,
            offset=offset
        )

    async def get_task(self, task_id: int, user_id: int):
        """Get single task by ID."""
        task = await self.repo.get_by_id(task_id, user_id)
        if not task:
            raise TaskNotFoundError(task_id)
        return task

    async def complete_task(self, task_id: int, user_id: int):
        """Mark task as completed."""
        task = await self.get_task(task_id, user_id)
        task.status = TaskStatus.COMPLETED
        task.reminder_at = None  # Clear reminder
        return task

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task."""
        deleted = await self.repo.delete(task_id, user_id)
        if not deleted:
            raise TaskNotFoundError(task_id)
        return True

    async def get_pending_reminders(self, before: datetime):
        """Get tasks with reminders due."""
        return await self.repo.get_due_reminders(before)
