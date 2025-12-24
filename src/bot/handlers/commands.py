# src/bot/handlers/commands.py
"""Basic command handlers: /start, /help, /status, /settings."""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.core.constants import MSG_WELCOME, MSG_HELP, BOT_NAME, BOT_VERSION
from src.bot.keyboards.inline import get_main_menu_keyboard, get_settings_keyboard
from src.database import async_session_factory, TaskRepository, TaskStatus

commands_router = Router(name="commands")


@commands_router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        MSG_WELCOME.format(bot_name=BOT_NAME),
        reply_markup=get_main_menu_keyboard()
    )


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(MSG_HELP)


@commands_router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show bot status."""
    async with async_session_factory() as session:
        repo = TaskRepository(session)
        user_id = message.from_user.id
        pending = await repo.get_all_by_user(user_id, TaskStatus.PENDING, limit=100)
        completed = await repo.get_all_by_user(user_id, TaskStatus.COMPLETED, limit=100)

    status_text = f"""*Bot Status*

*Version:* {BOT_VERSION}
*Your Tasks:*
- Pending: {len(pending)}
- Completed: {len(completed)}

Use /tasks to view your tasks."""
    await message.answer(status_text)


@commands_router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Handle /settings command."""
    await message.answer(
        "*Settings*\n\nConfigure your preferences:",
        reply_markup=get_settings_keyboard()
    )
