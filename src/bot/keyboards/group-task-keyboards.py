# src/bot/keyboards/group-task-keyboards.py
"""Inline keyboards for group task management."""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class GroupTaskCallback(CallbackData, prefix="gtask"):
    """Callback data for group task actions."""
    action: str
    task_id: int


def get_skip_button(field: str) -> InlineKeyboardMarkup:
    """Get skip button for optional fields."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Skip", callback_data=f"skip_{field}")
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirm/cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data="confirm_task")
    builder.button(text="❌ Cancel", callback_data="cancel_task")
    builder.adjust(2)
    return builder.as_markup()


def get_task_actions_keyboard(
    task_id: int, is_assignee: bool, is_admin: bool
) -> InlineKeyboardMarkup:
    """Get action buttons for a task."""
    builder = InlineKeyboardBuilder()

    if is_assignee:
        builder.button(
            text="✅ Mark Done",
            callback_data=GroupTaskCallback(action="done", task_id=task_id).pack()
        )

    if is_admin:
        builder.button(
            text="✏️ Edit",
            callback_data=GroupTaskCallback(action="edit", task_id=task_id).pack()
        )
        builder.button(
            text="🔄 Reassign",
            callback_data=GroupTaskCallback(action="reassign", task_id=task_id).pack()
        )

    builder.adjust(2)
    return builder.as_markup()


def get_verify_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Get verify/reject keyboard for admin."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Verify",
        callback_data=GroupTaskCallback(action="verify", task_id=task_id).pack()
    )
    builder.button(
        text="❌ Reject",
        callback_data=GroupTaskCallback(action="reject", task_id=task_id).pack()
    )
    builder.adjust(2)
    return builder.as_markup()


def get_task_list_keyboard(
    tasks: list, page: int = 0, page_size: int = 5
) -> InlineKeyboardMarkup:
    """Get paginated task list keyboard."""
    builder = InlineKeyboardBuilder()

    start = page * page_size
    end = start + page_size
    page_tasks = tasks[start:end]

    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "submitted": "📤",
        "completed": "✅",
        "overdue": "🚨",
        "cancelled": "🚫",
    }

    for task in page_tasks:
        emoji = status_emoji.get(task.status.value, "❓")
        # Truncate title to fit button
        title = task.title[:28] + "..." if len(task.title) > 28 else task.title

        builder.button(
            text=f"{emoji} {title}",
            callback_data=GroupTaskCallback(action="view", task_id=task.id).pack()
        )

    builder.adjust(1)

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}")
        )
    if end < len(tasks):
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def get_edit_field_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for selecting which field to edit.

    Per plan validation: /edit allows title + deadline only.
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📝 Title",
        callback_data=GroupTaskCallback(action="edit_title", task_id=task_id).pack()
    )
    builder.button(
        text="📅 Deadline",
        callback_data=GroupTaskCallback(action="edit_deadline", task_id=task_id).pack()
    )
    builder.button(
        text="❌ Cancel",
        callback_data=GroupTaskCallback(action="cancel_edit", task_id=task_id).pack()
    )
    builder.adjust(2)
    return builder.as_markup()
