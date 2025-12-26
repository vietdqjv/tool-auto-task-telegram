# src/bot/handlers/commands.py
"""Basic command handlers: /start, /help, /status, /settings."""
import importlib

from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.core.constants import MSG_WELCOME, MSG_HELP, BOT_NAME, BOT_VERSION
from src.bot.keyboards.inline import get_main_menu_keyboard, get_settings_keyboard
from src.database import async_session_factory, TaskRepository, TaskStatus

# Import for kebab-case modules
deep_link_helper = importlib.import_module("src.bot.utils.deep-link-helper")
dm_task_fsm = importlib.import_module("src.bot.handlers.dm-task-fsm")

commands_router = Router(name="commands")


@commands_router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, command: CommandObject, state: FSMContext):
    """Handle /start with deep link payload - routes to correct FSM."""
    # Only handle deep links in private chat
    if message.chat.type != "private" or not command.args:
        return await _cmd_start_normal(message)

    parsed = deep_link_helper.parse_fsm_payload(command.args)
    if not parsed:
        return await _cmd_start_normal(message)

    # Store context for DM FSM
    await state.update_data(
        source_group_id=parsed["group_id"],
        creator_id=message.from_user.id,
        task_id=parsed.get("task_id")
    )

    # Route to correct FSM
    if parsed["command"] == "newtask":
        await state.set_state(dm_task_fsm.NewTaskFSM.title)
        await message.answer(
            "<b>Tao Task Moi</b>\n\n<b>Buoc 1/3:</b> Nhap tieu de:",
            parse_mode="HTML"
        )
    elif parsed["command"] == "edittask":
        if not parsed.get("task_id"):
            await message.answer("Loi: Khong co task ID.")
            return
        await state.set_state(dm_task_fsm.EditTaskFSM.select_field)
        await message.answer(
            "<b>Sua Task</b>\n\nChon truong can sua:",
            reply_markup=dm_task_fsm.get_edit_field_keyboard(),
            parse_mode="HTML"
        )
    elif parsed["command"] == "bulktask":
        await state.set_state(dm_task_fsm.BulkTaskFSM.input_tasks)
        await message.answer(
            "<b>Tao Hang Loat</b>\n\nNhap danh sach task (moi dong 1 task):",
            parse_mode="HTML"
        )


@commands_router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command without deep link."""
    await _cmd_start_normal(message)


async def _cmd_start_normal(message: Message):
    """Normal start command handler."""
    is_group = message.chat.type in ["group", "supergroup"]
    if is_group:
        await message.reply(
            f"{message.from_user.mention_html()}\n{MSG_WELCOME.format(bot_name=BOT_NAME)}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            MSG_WELCOME.format(bot_name=BOT_NAME),
            reply_markup=get_main_menu_keyboard()
        )


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    is_group = message.chat.type in ["group", "supergroup"]
    if is_group:
        await message.reply(
            f"{message.from_user.mention_html()}\n{MSG_HELP}",
            parse_mode="HTML"
        )
    else:
        await message.answer(MSG_HELP)


@commands_router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show bot status."""
    async with async_session_factory() as session:
        repo = TaskRepository(session)
        user_id = message.from_user.id
        pending = await repo.get_all_by_user(user_id, TaskStatus.PENDING, limit=100)
        completed = await repo.get_all_by_user(user_id, TaskStatus.COMPLETED, limit=100)

    status_text = f"""<b>Bot Status</b>

<b>Version:</b> {BOT_VERSION}
<b>Your Tasks:</b>
- Pending: {len(pending)}
- Completed: {len(completed)}

Use /tasks to view your tasks."""

    is_group = message.chat.type in ["group", "supergroup"]
    if is_group:
        await message.reply(
            f"{message.from_user.mention_html()}\n{status_text}",
            parse_mode="HTML"
        )
    else:
        await message.answer(status_text, parse_mode="HTML")


@commands_router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Handle /settings command."""
    is_group = message.chat.type in ["group", "supergroup"]
    if is_group:
        await message.reply(
            f"{message.from_user.mention_html()}\n<b>Settings</b>\n\nConfigure your preferences:",
            reply_markup=get_settings_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "<b>Settings</b>\n\nConfigure your preferences:",
            reply_markup=get_settings_keyboard(),
            parse_mode="HTML"
        )
