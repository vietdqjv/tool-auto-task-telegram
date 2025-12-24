# src/database/repositories/__init__.py
"""Repository exports."""
import importlib

# Import kebab-case files using importlib
_user_repo = importlib.import_module(".user-repo", package=__name__)
_task_repo = importlib.import_module(".task-repo", package=__name__)

UserRepository = _user_repo.UserRepository
TaskRepository = _task_repo.TaskRepository

__all__ = ["UserRepository", "TaskRepository"]
