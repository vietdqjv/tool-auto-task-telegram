# src/bot/handlers/__init__.py
"""Handler router exports."""
from .commands import commands_router
from .tasks import tasks_router
from .callbacks import callbacks_router

__all__ = ["commands_router", "tasks_router", "callbacks_router"]
