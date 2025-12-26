# src/bot/handlers/group-tasks.py
"""Command handlers for group task management."""
import importlib
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from src.core.config import settings
from src.database.models.task import TaskStatus

# Import with kebab-case support
keyboards = importlib.import_module("src.bot.keyboards.group-task-keyboards")
gts = importlib.import_module("src.services.group-task-service")
wh = importlib.import_module("src.services.working-hours")

GroupTaskService = gts.GroupTaskService
GroupTaskCallback = keyboards.GroupTaskCallback
TIMEZONE = ZoneInfo(settings.TIMEZONE)

group_tasks_router = Router(name="group_tasks")


# ============ View Commands ============

@group_tasks_router.message(Command("assign"))
async def cmd_assign(message: Message, session: AsyncSession):
    """Assign a new task to a user (admin only).

    Usage: /assign @user Task title
    """
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    # Check admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể giao task.")
        return

    # Parse command: /assign @user Task title
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Sử dụng: /assign @user Tiêu đề task")
        return

    # Get assignee from mention
    assignee_id = None
    assignee_name = "User"
    for entity in message.entities or []:
        if entity.type == "text_mention" and entity.user:
            assignee_id = entity.user.id
            assignee_name = entity.user.full_name
            break
        elif entity.type == "mention":
            # @username mention - can't get user_id directly
            await message.answer(
                "Vui lòng mention trực tiếp user (không dùng @username).\n"
                "Ví dụ: Gõ @ rồi chọn user từ danh sách."
            )
            return

    if not assignee_id:
        await message.answer("Vui lòng mention người nhận task.\nVí dụ: /assign @user Tiêu đề task")
        return

    # Extract title (everything after @mention)
    title = args[2].strip()
    if not title:
        await message.answer("Vui lòng nhập tiêu đề task.")
        return

    service = GroupTaskService(session)
    try:
        task = await service.create_group_task(
            group_id=message.chat.id,
            title=title,
            assignee_id=assignee_id,
            assigned_by_id=message.from_user.id,
        )
        await session.commit()
        await message.answer(
            f"✅ Task đã tạo!\n\n"
            f"📋 <b>ID:</b> {task.id}\n"
            f"📝 <b>Tiêu đề:</b> {task.title}\n"
            f'👤 <b>Giao cho:</b> <a href="tg://user?id={assignee_id}">{assignee_name}</a>\n\n'
            f"Người nhận có thể hoàn thành với /done {task.id}",
            parse_mode="HTML",
        )
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


@group_tasks_router.message(Command("mytasks"))
async def cmd_my_tasks(message: Message, session: AsyncSession):
    """View tasks assigned to me."""
    service = GroupTaskService(session)
    group_id = message.chat.id if message.chat.type in ["group", "supergroup"] else None
    tasks = await service.get_user_tasks(message.from_user.id, group_id)

    if not tasks:
        await message.answer("Bạn không có task nào.")
        return

    await message.answer(
        f"📋 Task của bạn ({len(tasks)}):",
        reply_markup=keyboards.get_task_list_keyboard(tasks),
    )


@group_tasks_router.message(Command("tasks"))
async def cmd_all_tasks(message: Message, session: AsyncSession):
    """View all group tasks (admin only)."""
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    # Check admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể xem tất cả task.")
        return

    service = GroupTaskService(session)
    tasks = await service.get_group_tasks(message.chat.id)

    if not tasks:
        await message.answer("Không có task nào trong nhóm này.")
        return

    await message.answer(
        f"📋 Task nhóm ({len(tasks)}):",
        reply_markup=keyboards.get_task_list_keyboard(tasks),
    )


# ============ Completion Workflow ============

@group_tasks_router.message(Command("done"))
async def cmd_done(message: Message, session: AsyncSession):
    """Submit task for verification (assignee only)."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Sử dụng: /done <task_id>")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID không hợp lệ.")
        return

    service = GroupTaskService(session)
    try:
        task = await service.submit_task(task_id, message.from_user.id)
        await session.commit()

        # Notify admin
        await message.answer(
            f"✅ Task đã gửi để xác nhận!\n\n"
            f"📋 {task.title}\n"
            f"Đang chờ admin xác nhận.",
        )

        # Send notification to group with verify buttons
        if task.group_id:
            await message.bot.send_message(
                task.group_id,
                f"📤 Task đã Submit\n\n"
                f"📋 {task.title}\n"
                f"👤 Bởi: {message.from_user.mention_html()}\n\n"
                f"Admin, vui lòng xác nhận:",
                reply_markup=keyboards.get_verify_keyboard(task_id),
                parse_mode="HTML",
            )
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


@group_tasks_router.message(Command("verify"))
async def cmd_verify(message: Message, session: AsyncSession):
    """Verify completed task (admin only)."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Sử dụng: /verify <task_id>")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID không hợp lệ.")
        return

    # Check admin - must be in group
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể xác nhận task.")
        return

    service = GroupTaskService(session)
    try:
        task = await service.verify_task(task_id, message.from_user.id)
        await session.commit()
        await message.answer(
            f"✅ Task đã xác nhận!\n\n"
            f"📋 {task.title}\n"
            f'👤 Hoàn thành bởi: <a href="tg://user?id={task.assignee_id}">Assignee</a>',
            parse_mode="HTML",
        )
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


@group_tasks_router.message(Command("reject"))
async def cmd_reject(message: Message, session: AsyncSession):
    """Reject task submission (admin only)."""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Sử dụng: /reject <task_id> [lý do]")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID không hợp lệ.")
        return

    reason = " ".join(args[2:]) if len(args) > 2 else None

    # Check admin - must be in group
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể từ chối task.")
        return

    service = GroupTaskService(session)
    try:
        task = await service.reject_task(task_id, message.from_user.id)
        await session.commit()

        # Notify assignee
        if task.group_id:
            await message.bot.send_message(
                task.group_id,
                f"❌ Task bị từ chối\n\n"
                f"📋 {task.title}\n"
                f'👤 <a href="tg://user?id={task.assignee_id}">Assignee</a>\n'
                f"📝 Lý do: {reason or 'Không nêu'}\n\n"
                f"Vui lòng cập nhật và gửi lại với /done {task_id}",
                parse_mode="HTML",
            )
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


# ============ Reminder ============

@group_tasks_router.message(Command("rep"))
async def cmd_set_reminder(message: Message, session: AsyncSession):
    """Set reminder interval for a task."""
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Sử dụng: /rep <task_id> <interval>\n"
            "Ví dụ: /rep 123 2h, /rep 123 30m, /rep 123 1h30m"
        )
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID không hợp lệ.")
        return

    interval = wh.parse_reminder_interval(args[2])
    if not interval:
        await message.answer(
            f"Định dạng không hợp lệ hoặc dưới {settings.MIN_REMINDER_INTERVAL} phút.\n"
            "Dùng: 2h, 30m, 1h30m"
        )
        return

    service = GroupTaskService(session)
    try:
        task = await service.update_reminder_interval(task_id, interval)
        await session.commit()
        hours, mins = divmod(interval, 60)
        if hours and mins:
            interval_text = f"{hours}h {mins}m"
        elif hours:
            interval_text = f"{hours}h"
        else:
            interval_text = f"{mins}m"
        await message.answer(f"⏰ Nhắc nhở đã đặt mỗi {interval_text}")
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


# ============ Reassign ============

@group_tasks_router.message(Command("reassign"))
async def cmd_reassign(message: Message, session: AsyncSession):
    """Reassign task to different user (admin only)."""
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Sử dụng: /reassign <task_id> @new_user")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Task ID không hợp lệ.")
        return

    # Check admin - must be in group
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Lệnh này chỉ hoạt động trong nhóm.")
        return

    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("Chỉ admin mới có thể chuyển giao task.")
        return

    # Get new assignee from mention
    new_assignee_id = None
    for entity in message.entities or []:
        if entity.type == "text_mention" and entity.user:
            new_assignee_id = entity.user.id
            break

    if not new_assignee_id:
        await message.answer("Vui lòng mention người nhận mới với @username")
        return

    service = GroupTaskService(session)
    try:
        task = await service.reassign_task(task_id, new_assignee_id, message.from_user.id)
        await session.commit()
        await message.answer(
            f"🔄 Task đã chuyển giao!\n\n"
            f"📋 {task.title}\n"
            f'👤 Người nhận mới: <a href="tg://user?id={new_assignee_id}">Assignee</a>',
            parse_mode="HTML",
        )
    except Exception as e:
        await session.rollback()
        await message.answer(f"Lỗi: {e}")


# ============ Callback Handlers ============

@group_tasks_router.callback_query(GroupTaskCallback.filter(F.action == "view"))
async def view_task_callback(
    callback: CallbackQuery,
    callback_data: GroupTaskCallback,
    session: AsyncSession,
):
    """View task details."""
    service = GroupTaskService(session)
    task = await service.get_task_by_id(callback_data.task_id)

    if not task:
        await callback.answer("Task không tìm thấy.", show_alert=True)
        return

    status_map = {
        "pending": "⏳ Chờ xử lý",
        "in_progress": "🔄 Đang thực hiện",
        "submitted": "📤 Đã gửi",
        "completed": "✅ Hoàn thành",
        "overdue": "🚨 Quá hạn",
        "cancelled": "🚫 Đã hủy",
    }
    status_text = status_map.get(task.status.value, task.status.value)

    is_assignee = callback.from_user.id == task.assignee_id
    is_admin = False
    if callback.message.chat.type in ["group", "supergroup"]:
        member = await callback.message.chat.get_member(callback.from_user.id)
        is_admin = member.status in ["creator", "administrator"]

    deadline_str = task.due_date.strftime('%d/%m/%Y %H:%M') if task.due_date else "Không"

    await callback.message.edit_text(
        f"📋 <b>Chi tiết Task</b>\n\n"
        f"<b>ID:</b> {task.id}\n"
        f"<b>Tiêu đề:</b> {task.title}\n"
        f"<b>Trạng thái:</b> {status_text}\n"
        f"<b>Mô tả:</b> {task.description or 'Không'}\n"
        f"<b>Deadline:</b> {deadline_str}\n"
        f'<b>Assignee:</b> <a href="tg://user?id={task.assignee_id}">User</a>\n',
        reply_markup=keyboards.get_task_actions_keyboard(task.id, is_assignee, is_admin),
        parse_mode="HTML",
    )
    await callback.answer()


@group_tasks_router.callback_query(GroupTaskCallback.filter(F.action == "done"))
async def done_task_callback(
    callback: CallbackQuery,
    callback_data: GroupTaskCallback,
    session: AsyncSession,
):
    """Mark task as done from callback button."""
    service = GroupTaskService(session)
    try:
        task = await service.submit_task(callback_data.task_id, callback.from_user.id)
        await session.commit()
        await callback.message.edit_text(
            f"📤 Task đã Submit\n\n"
            f"📋 {task.title}\n"
            f"👤 Bởi: {callback.from_user.mention_html()}\n\n"
            f"Đang chờ admin xác nhận:",
            reply_markup=keyboards.get_verify_keyboard(task.id),
            parse_mode="HTML",
        )
        await callback.answer("Task đã gửi!")
    except Exception as e:
        await session.rollback()
        await callback.answer(str(e), show_alert=True)


@group_tasks_router.callback_query(GroupTaskCallback.filter(F.action == "verify"))
async def verify_task_callback(
    callback: CallbackQuery,
    callback_data: GroupTaskCallback,
    session: AsyncSession,
):
    """Verify task from callback button."""
    if callback.message.chat.type in ["group", "supergroup"]:
        member = await callback.message.chat.get_member(callback.from_user.id)
        if member.status not in ["creator", "administrator"]:
            await callback.answer("Chỉ admin mới có thể xác nhận.", show_alert=True)
            return

    service = GroupTaskService(session)
    try:
        task = await service.verify_task(callback_data.task_id, callback.from_user.id)
        await session.commit()
        await callback.message.edit_text(
            f"✅ Task đã xác nhận!\n\n"
            f"📋 {task.title}\n"
            f"Xác nhận bởi: {callback.from_user.mention_html()}",
            parse_mode="HTML",
        )
        await callback.answer("Task đã xác nhận!")
    except Exception as e:
        await session.rollback()
        await callback.answer(str(e), show_alert=True)


@group_tasks_router.callback_query(GroupTaskCallback.filter(F.action == "reject"))
async def reject_task_callback(
    callback: CallbackQuery,
    callback_data: GroupTaskCallback,
    session: AsyncSession,
):
    """Reject task from callback button."""
    if callback.message.chat.type in ["group", "supergroup"]:
        member = await callback.message.chat.get_member(callback.from_user.id)
        if member.status not in ["creator", "administrator"]:
            await callback.answer("Chỉ admin mới có thể từ chối.", show_alert=True)
            return

    service = GroupTaskService(session)
    try:
        task = await service.reject_task(callback_data.task_id, callback.from_user.id)
        await session.commit()
        await callback.message.edit_text(
            f"❌ Task bị từ chối\n\n"
            f"📋 {task.title}\n"
            f"Từ chối bởi: {callback.from_user.mention_html()}\n\n"
            f"Assignee: Vui lòng cập nhật và /done {task.id}",
            parse_mode="HTML",
        )
        await callback.answer("Task đã từ chối.")
    except Exception as e:
        await session.rollback()
        await callback.answer(str(e), show_alert=True)
