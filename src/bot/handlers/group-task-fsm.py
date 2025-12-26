# src/bot/handlers/group-task-fsm.py
"""FSM states and handlers for group task creation."""
import importlib
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from zoneinfo import ZoneInfo

from src.core.config import settings

# Import modules using importlib for kebab-case
keyboards = importlib.import_module("src.bot.keyboards.group-task-keyboards")
deep_link_helper = importlib.import_module("src.bot.utils.deep-link-helper")

TIMEZONE = ZoneInfo(settings.TIMEZONE)

group_task_fsm_router = Router(name="group_task_fsm")


class CreateGroupTask(StatesGroup):
    """States for group task creation FSM."""
    select_assignee = State()
    enter_title = State()
    enter_description = State()
    select_deadline = State()
    set_reminder = State()
    confirm = State()


class EditGroupTask(StatesGroup):
    """States for editing group task.

    Per plan validation: /edit allows title + deadline only.
    """
    select_field = State()
    edit_title = State()
    edit_deadline = State()


# ============ Create Task Flow ============

@group_task_fsm_router.message(Command("task"))
async def cmd_task_start(message: Message, state: FSMContext):
    """Start task creation FSM (admin only in group)."""
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể tạo task.")
        return

    await state.set_state(CreateGroupTask.select_assignee)
    await state.update_data(group_id=message.chat.id, admin_id=message.from_user.id)
    await message.answer(
        "👤 Tag người bạn muốn giao task:\n"
        "Ví dụ: @username"
    )


@group_task_fsm_router.message(CreateGroupTask.select_assignee)
async def process_assignee(message: Message, state: FSMContext):
    """Process assignee selection."""
    if not message.entities:
        await message.answer("Vui lòng tag một user với @username")
        return

    for entity in message.entities:
        if entity.type == "text_mention" and entity.user:
            # Direct mention with user object
            await state.update_data(
                assignee_id=entity.user.id,
                assignee_name=entity.user.full_name,
            )
            await state.set_state(CreateGroupTask.enter_title)
            await message.answer("📝 Nhập tiêu đề task:")
            return
        elif entity.type == "mention":
            # @username mention - store for later resolution
            mention = message.text[entity.offset:entity.offset + entity.length]
            await state.update_data(assignee_mention=mention)
            await state.set_state(CreateGroupTask.enter_title)
            await message.answer("📝 Nhập tiêu đề task:")
            return

    await message.answer("Vui lòng tag một user với @username")


@group_task_fsm_router.message(CreateGroupTask.enter_title)
async def process_title(message: Message, state: FSMContext):
    """Process task title."""
    title = message.text.strip()
    if len(title) < 3:
        await message.answer("Tiêu đề phải có ít nhất 3 ký tự.")
        return
    if len(title) > 255:
        await message.answer("Tiêu đề quá dài (tối đa 255 ký tự).")
        return

    await state.update_data(title=title)
    await state.set_state(CreateGroupTask.enter_description)
    await message.answer(
        "📄 Nhập mô tả (hoặc bấm Skip):",
        reply_markup=keyboards.get_skip_button("description"),
    )


@group_task_fsm_router.callback_query(
    CreateGroupTask.enter_description,
    F.data == "skip_description"
)
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Skip description."""
    await state.update_data(description=None)
    await state.set_state(CreateGroupTask.select_deadline)
    await callback.message.edit_text(
        "📅 Nhập deadline:\n"
        "Định dạng: DD/MM HH:MM hoặc DD/MM/YYYY HH:MM\n"
        "Ví dụ: 25/12 17:00"
    )
    await callback.answer()


@group_task_fsm_router.message(CreateGroupTask.enter_description)
async def process_description(message: Message, state: FSMContext):
    """Process task description."""
    await state.update_data(description=message.text)
    await state.set_state(CreateGroupTask.select_deadline)
    await message.answer(
        "📅 Nhập deadline:\n"
        "Định dạng: DD/MM HH:MM hoặc DD/MM/YYYY HH:MM\n"
        "Ví dụ: 25/12 17:00"
    )


@group_task_fsm_router.message(CreateGroupTask.select_deadline)
async def process_deadline(message: Message, state: FSMContext):
    """Process deadline input."""
    text = message.text.strip()

    # Try parsing formats
    formats = [
        "%d/%m %H:%M",
        "%d/%m/%Y %H:%M",
    ]

    due_date = None
    for fmt in formats:
        try:
            due_date = datetime.strptime(text, fmt)
            if "%Y" not in fmt:
                due_date = due_date.replace(year=datetime.now().year)
            due_date = due_date.replace(tzinfo=TIMEZONE)
            break
        except ValueError:
            continue

    if not due_date:
        await message.answer(
            "Định dạng không hợp lệ. Vui lòng dùng DD/MM HH:MM\n"
            "Ví dụ: 25/12 17:00"
        )
        return

    if due_date <= datetime.now(TIMEZONE):
        await message.answer("Deadline phải ở tương lai.")
        return

    await state.update_data(due_date=due_date.isoformat())
    await state.set_state(CreateGroupTask.set_reminder)
    await message.answer(
        "⏰ Đặt khoảng thời gian nhắc nhở (hoặc Skip):\n"
        "Định dạng: 2h, 30m, 1h30m\n"
        f"Tối thiểu: {settings.MIN_REMINDER_INTERVAL} phút",
        reply_markup=keyboards.get_skip_button("reminder"),
    )


@group_task_fsm_router.callback_query(
    CreateGroupTask.set_reminder,
    F.data == "skip_reminder"
)
async def skip_reminder(callback: CallbackQuery, state: FSMContext):
    """Skip reminder setting."""
    await state.update_data(reminder_interval=None)
    await show_confirmation(callback.message, state)
    await callback.answer()


@group_task_fsm_router.message(CreateGroupTask.set_reminder)
async def process_reminder(message: Message, state: FSMContext):
    """Process reminder interval."""
    wh = importlib.import_module("src.services.working-hours")

    interval = wh.parse_reminder_interval(message.text)
    if not interval:
        await message.answer(
            f"Định dạng không hợp lệ hoặc dưới {settings.MIN_REMINDER_INTERVAL} phút.\n"
            "Dùng: 2h, 30m, 1h30m"
        )
        return

    await state.update_data(reminder_interval=interval)
    await show_confirmation(message, state)


async def show_confirmation(message: Message, state: FSMContext):
    """Show task confirmation."""
    data = await state.get_data()

    reminder_text = "Không"
    if data.get("reminder_interval"):
        hours, mins = divmod(data["reminder_interval"], 60)
        if hours and mins:
            reminder_text = f"{hours}h {mins}m"
        elif hours:
            reminder_text = f"{hours}h"
        else:
            reminder_text = f"{mins}m"

    # Format deadline
    deadline_str = data.get("due_date", "N/A")
    if deadline_str != "N/A":
        try:
            dt = datetime.fromisoformat(deadline_str)
            deadline_str = dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            pass

    assignee = data.get("assignee_name") or data.get("assignee_mention", "N/A")

    await state.set_state(CreateGroupTask.confirm)
    await message.answer(
        f"📋 <b>Xác nhận Task</b>\n\n"
        f"👤 Giao cho: {assignee}\n"
        f"📝 Tiêu đề: {data['title']}\n"
        f"📄 Mô tả: {data.get('description') or 'Không'}\n"
        f"📅 Deadline: {deadline_str}\n"
        f"⏰ Nhắc nhở: {reminder_text}\n\n"
        f"Xác nhận tạo task?",
        reply_markup=keyboards.get_confirm_keyboard(),
        parse_mode="HTML",
    )


@group_task_fsm_router.callback_query(CreateGroupTask.confirm, F.data == "confirm_task")
async def confirm_create_task(
    callback: CallbackQuery,
    state: FSMContext,
    session,  # Injected by middleware (AsyncSession)
):
    """Create the task after confirmation using GroupTaskService."""
    gts = importlib.import_module("src.services.group-task-service")
    GroupTaskService = gts.GroupTaskService

    data = await state.get_data()
    service = GroupTaskService(session)

    # Parse due_date from ISO format
    due_date = None
    if data.get("due_date"):
        due_date = datetime.fromisoformat(data["due_date"])

    # Get assignee_id (may need resolution for @mention)
    assignee_id = data.get("assignee_id")
    if not assignee_id:
        # For @username mention, we can't resolve without API call
        # Use the admin's ID as placeholder and notify them
        await callback.message.edit_text(
            "⚠️ Không thể xác định user từ @username.\n"
            "Vui lòng tag user trực tiếp (không phải @username)."
        )
        await state.clear()
        await callback.answer()
        return

    try:
        task = await service.create_group_task(
            group_id=data["group_id"],
            title=data["title"],
            assignee_id=assignee_id,
            assigned_by_id=data["admin_id"],
            description=data.get("description"),
            due_date=due_date,
            reminder_interval_minutes=data.get("reminder_interval"),
        )
        await session.commit()

        await callback.message.edit_text(
            f"✅ Task đã được tạo!\n\n"
            f"🆔 ID: {task.id}\n"
            f"📋 {task.title}\n"
            f'👤 Giao cho: <a href="tg://user?id={task.assignee_id}">Assignee</a>',
            parse_mode="HTML",
        )
        await callback.answer("Task đã tạo!")
    except Exception as e:
        await session.rollback()
        await callback.message.edit_text(f"❌ Lỗi: {e}")
        await callback.answer()

    await state.clear()


@group_task_fsm_router.callback_query(CreateGroupTask.confirm, F.data == "cancel_task")
async def cancel_create_task(callback: CallbackQuery, state: FSMContext):
    """Cancel task creation."""
    await state.clear()
    await callback.message.edit_text("❌ Đã hủy tạo task.")
    await callback.answer()


# ============ Cancel Command ============

@group_task_fsm_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel any ongoing FSM flow."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Khong co gi de huy.")
        return

    await state.clear()
    await message.answer("Da huy thao tac.")


# ============ DM Redirect Handlers ============

async def _redirect_to_dm(message: Message, bot: Bot, command: str, task_id: int | None = None):
    """Generic redirect handler for FSM commands -> DM."""
    link = await deep_link_helper.create_fsm_link(bot, command, message.chat.id, task_id)

    action_text = {"newtask": "Tao Task", "edittask": "Sua Task", "bulktask": "Tao Hang Loat"}
    await message.reply(
        f"{message.from_user.mention_html()}\n"
        f"Nhan nut ben duoi de {action_text[command].lower()} trong DM:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"{action_text[command]}", url=link)
        ]]),
        parse_mode="HTML"
    )


@group_task_fsm_router.message(Command("newtask"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_newtask_redirect(message: Message, bot: Bot):
    """Redirect /newtask to DM via deep link."""
    await _redirect_to_dm(message, bot, "newtask")


@group_task_fsm_router.message(Command("edittask"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_edittask_redirect(message: Message, bot: Bot):
    """Redirect /edittask to DM via deep link."""
    # Parse task_id from command args: /edittask 123
    task_id = None
    parts = message.text.split()
    if len(parts) > 1:
        try:
            task_id = int(parts[1])
        except ValueError:
            pass
    await _redirect_to_dm(message, bot, "edittask", task_id)


@group_task_fsm_router.message(Command("bulktask"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_bulktask_redirect(message: Message, bot: Bot):
    """Redirect /bulktask to DM via deep link."""
    await _redirect_to_dm(message, bot, "bulktask")
