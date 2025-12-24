# src/bot/handlers/callbacks.py
"""Callback query handlers for inline buttons."""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.core.constants import MSG_CONFIRM_DELETE
from src.database import async_session_factory
from src.bot.keyboards.inline import TaskCallback, get_confirm_delete_keyboard
import importlib

callbacks_router = Router(name="callbacks")

# Import kebab-case service
_task_service = importlib.import_module("src.services.task-service")
TaskService = _task_service.TaskService


@callbacks_router.callback_query(TaskCallback.filter(F.action == "view"))
async def callback_view_task(callback: CallbackQuery, callback_data: TaskCallback):
    """View task details."""
    async with async_session_factory() as session:
        service = TaskService(session)
        try:
            task = await service.get_task(callback_data.task_id, callback.from_user.id)
            due = task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set'
            text = f"*Task Details*\n\n*Title:* {task.title}\n*Status:* {task.status.value}\n*Priority:* {task.priority.value}\n*Due:* {due}\n*ID:* `{task.id}`"
            await callback.message.edit_text(text)
        except Exception as e:
            await callback.answer(f"Error: {e}", show_alert=True)
    await callback.answer()


@callbacks_router.callback_query(TaskCallback.filter(F.action == "complete"))
async def callback_complete_task(callback: CallbackQuery, callback_data: TaskCallback):
    """Mark task as completed."""
    async with async_session_factory() as session:
        service = TaskService(session)
        try:
            task = await service.complete_task(callback_data.task_id, callback.from_user.id)
            await session.commit()
            await callback.answer(f"Task '{task.title}' completed!")
            await callback.message.delete()
        except Exception as e:
            await callback.answer(f"Error: {e}", show_alert=True)


@callbacks_router.callback_query(TaskCallback.filter(F.action == "delete"))
async def callback_delete_confirm(callback: CallbackQuery, callback_data: TaskCallback):
    """Show delete confirmation."""
    async with async_session_factory() as session:
        service = TaskService(session)
        task = await service.get_task(callback_data.task_id, callback.from_user.id)
        await callback.message.edit_text(
            MSG_CONFIRM_DELETE.format(title=task.title),
            reply_markup=get_confirm_delete_keyboard(task.id)
        )
    await callback.answer()


@callbacks_router.callback_query(TaskCallback.filter(F.action == "confirm_delete"))
async def callback_delete_task(callback: CallbackQuery, callback_data: TaskCallback):
    """Actually delete the task."""
    async with async_session_factory() as session:
        service = TaskService(session)
        await service.delete_task(callback_data.task_id, callback.from_user.id)
        await session.commit()
    await callback.answer("Task deleted!")
    await callback.message.delete()


@callbacks_router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery):
    """Cancel current operation."""
    await callback.message.delete()
    await callback.answer("Cancelled")
