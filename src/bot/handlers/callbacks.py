# src/bot/handlers/callbacks.py
"""Callback query handlers for inline buttons."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.core.constants import MSG_CONFIRM_DELETE, MSG_HELP
from src.database import async_session_factory, TaskRepository, TaskStatus
from src.bot.keyboards.inline import TaskCallback, get_confirm_delete_keyboard, get_task_list_keyboard
from src.fsm.task_fsm import AddTaskFSM
import importlib

callbacks_router = Router(name="callbacks")

# Import kebab-case service
_task_service = importlib.import_module("src.services.task-service")
TaskService = _task_service.TaskService


# === Main Menu Callbacks ===

@callbacks_router.callback_query(F.data == "menu_tasks")
async def callback_menu_tasks(callback: CallbackQuery):
    """Handle View Tasks button."""
    async with async_session_factory() as session:
        repo = TaskRepository(session)
        tasks = await repo.get_all_by_user(callback.from_user.id, limit=10)

    if not tasks:
        await callback.message.edit_text("You don't have any tasks yet.\n\nUse /add to create one!")
    else:
        text = "*Your Tasks:*\n\n"
        for i, task in enumerate(tasks[:10], 1):
            status_emoji = "✅" if task.status == TaskStatus.COMPLETED else "⏳"
            text += f"{i}. {status_emoji} {task.title}\n"
        await callback.message.edit_text(text, reply_markup=get_task_list_keyboard(tasks))
    await callback.answer()


@callbacks_router.callback_query(F.data == "menu_add")
async def callback_menu_add(callback: CallbackQuery, state: FSMContext):
    """Handle Add Task button - start FSM."""
    await state.set_state(AddTaskFSM.waiting_for_title)
    await callback.message.edit_text("*Create New Task*\n\nPlease enter the task title:")
    await callback.answer()


@callbacks_router.callback_query(F.data == "menu_help")
async def callback_menu_help(callback: CallbackQuery):
    """Handle Help button."""
    await callback.message.edit_text(MSG_HELP)
    await callback.answer()


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
