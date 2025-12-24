# src/database/repositories/task-repo.py
"""Task repository for database operations."""
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.task import Task, TaskStatus, TaskPriority


class TaskRepository:
    """Repository for Task CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, task_id: int, user_id: int | None = None) -> Task | None:
        """Get task by ID, optionally filter by user."""
        query = select(Task).where(Task.id == task_id)
        if user_id:
            query = query.where(Task.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_user(
        self,
        user_id: int,
        status: TaskStatus | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> list[Task]:
        """Get all tasks for user with optional filters."""
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: datetime | None = None,
        reminder_at: datetime | None = None
    ) -> Task:
        """Create new task."""
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            reminder_at=reminder_at
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def update_status(self, task_id: int, status: TaskStatus) -> Task | None:
        """Update task status."""
        task = await self.get_by_id(task_id)
        if task:
            task.status = status
            await self.session.flush()
        return task

    async def delete(self, task_id: int, user_id: int) -> bool:
        """Delete task. Returns True if deleted."""
        result = await self.session.execute(
            delete(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.rowcount > 0

    async def get_due_reminders(self, before: datetime) -> list[Task]:
        """Get tasks with reminders due before given time."""
        query = select(Task).where(
            Task.reminder_at <= before,
            Task.reminder_at.isnot(None),
            Task.status != TaskStatus.COMPLETED
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
