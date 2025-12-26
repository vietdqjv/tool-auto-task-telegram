# src/bot/handlers/__init__.py
"""Handler router exports."""
import importlib

from .commands import commands_router
from .tasks import tasks_router
from .callbacks import callbacks_router

# Group task handlers (kebab-case file names)
group_tasks = importlib.import_module("src.bot.handlers.group-tasks")
group_task_fsm = importlib.import_module("src.bot.handlers.group-task-fsm")
dm_task_fsm = importlib.import_module("src.bot.handlers.dm-task-fsm")

group_tasks_router = group_tasks.group_tasks_router
group_task_fsm_router = group_task_fsm.group_task_fsm_router
dm_task_fsm_router = dm_task_fsm.dm_task_fsm_router

__all__ = [
    "commands_router",
    "tasks_router",
    "callbacks_router",
    "group_tasks_router",
    "group_task_fsm_router",
    "dm_task_fsm_router",
]
