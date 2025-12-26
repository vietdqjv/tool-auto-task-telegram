# src/bot/handlers/tasks.py
"""Task management handlers with FSM."""
from datetime import datetime
import importlib
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from src.core.constants import MSG_NO_TASKS, MSG_TASK_CREATED, MSG_ERROR
from src.database import async_session_factory
from src.scheduler import get_scheduler
from src.bot.keyboards.inline import get_task_list_keyboard, get_cancel_keyboard

tasks_router = Router(name="tasks")
_task_service = importlib.import_module("src.services.task-service")
TaskService = _task_service.TaskService


class AddTaskStates(StatesGroup):
    title = State()
    due_date = State()
    reminder = State()


@tasks_router.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """List user's tasks."""
    async with async_session_factory() as session:
        tasks = await TaskService(session).get_user_tasks(message.from_user.id)
    if not tasks:
        return await message.answer(MSG_NO_TASKS)
    text = "*Your Tasks:*\n\n"
    for i, t in enumerate(tasks, 1):
        text += f"{i}. [{'v' if t.status.value == 'completed' else 'o'}] {t.title}\n"
    await message.answer(text, reply_markup=get_task_list_keyboard(tasks))


@tasks_router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    await state.set_state(AddTaskStates.title)
    await message.answer("*Step 1/3: Task Title*\n\nEnter task title:", reply_markup=get_cancel_keyboard())


@tasks_router.message(AddTaskStates.title)
async def process_title(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("Cancelled.")
    await state.update_data(title=message.text)
    await state.set_state(AddTaskStates.due_date)
    await message.answer("*Step 2/3: Due Date*\n\nEnter due date (YYYY-MM-DD) or 'skip':")


@tasks_router.message(AddTaskStates.due_date)
async def process_due_date(message: Message, state: FSMContext):
    due_date_str = None
    if message.text.lower() != "skip":
        try:
            datetime.strptime(message.text, "%Y-%m-%d")  # Validate format
            due_date_str = message.text  # Store as string for JSON serialization
        except ValueError:
            return await message.answer("Invalid format. Use YYYY-MM-DD or 'skip'.")
    await state.update_data(due_date=due_date_str)
    await state.set_state(AddTaskStates.reminder)
    await message.answer("*Step 3/3: Reminder*\n\nEnter reminder (YYYY-MM-DD HH:MM) or 'skip':")


@tasks_router.message(AddTaskStates.reminder)
async def process_reminder(message: Message, state: FSMContext):
    data = await state.get_data()
    reminder_at = None
    if message.text.lower() != "skip":
        try:
            reminder_at = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        except ValueError:
            return await message.answer("Invalid format. Use YYYY-MM-DD HH:MM or 'skip'.")
    await state.clear()
    # Convert due_date string back to datetime
    due_date = datetime.strptime(data["due_date"], "%Y-%m-%d") if data.get("due_date") else None
    async with async_session_factory() as session:
        service = TaskService(session)
        try:
            task = await service.create_task(
                user_id=message.from_user.id, title=data["title"],
                due_date=due_date, reminder_at=reminder_at)
            await session.commit()
            if reminder_at:
                get_scheduler().add_reminder(f"remind_{task.id}", reminder_at, message.from_user.id, task.id)
            due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "Not set"
            await message.answer(MSG_TASK_CREATED.format(title=task.title, due_date=due, task_id=task.id))
        except Exception as e:
            await message.answer(MSG_ERROR.format(error=str(e)))
