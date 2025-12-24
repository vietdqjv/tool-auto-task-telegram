# src/bot/keyboards/inline.py
"""Inline keyboard builders."""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


class TaskCallback(CallbackData, prefix="task"):
    """Callback data for task actions."""
    action: str
    task_id: int


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="View Tasks", callback_data="menu_tasks"),
        InlineKeyboardButton(text="Add Task", callback_data="menu_add"),
        InlineKeyboardButton(text="Help", callback_data="menu_help")
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_task_list_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """Keyboard with task action buttons."""
    builder = InlineKeyboardBuilder()
    for task in tasks[:5]:  # Limit to 5
        cb = TaskCallback(action="view", task_id=task.id)
        title = task.title[:20] + "..." if len(task.title) > 20 else task.title
        builder.add(InlineKeyboardButton(text=title, callback_data=cb.pack()))
    builder.adjust(1)
    return builder.as_markup()


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Actions for single task."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Complete",
            callback_data=TaskCallback(action="complete", task_id=task_id).pack()
        ),
        InlineKeyboardButton(
            text="Delete",
            callback_data=TaskCallback(action="delete", task_id=task_id).pack()
        ),
        InlineKeyboardButton(text="Cancel", callback_data="cancel")
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_confirm_delete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Confirmation for delete."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Yes, Delete",
            callback_data=TaskCallback(action="confirm_delete", task_id=task_id).pack()
        ),
        InlineKeyboardButton(text="Cancel", callback_data="cancel")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Language", callback_data="settings_lang"),
        InlineKeyboardButton(text="Notifications", callback_data="settings_notif"),
        InlineKeyboardButton(text="Back", callback_data="cancel")
    )
    builder.adjust(2, 1)
    return builder.as_markup()
