# src/bot/utils/deep-link-helper.py
"""Deep link utilities for group-to-DM redirection."""
from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link, decode_payload

# Supported FSM commands
FSM_COMMANDS = ["newtask", "edittask", "bulktask"]


async def create_fsm_link(
    bot: Bot, command: str, group_id: int, task_id: int | None = None
) -> str:
    """Create deep link for FSM command redirect.

    Args:
        bot: Bot instance
        command: FSM command (newtask, edittask, bulktask)
        group_id: Source group ID
        task_id: Optional task ID for edit

    Returns:
        Deep link URL with encoded payload
    """
    if task_id:
        payload = f"{command}_{group_id}_{task_id}"
    else:
        payload = f"{command}_{group_id}"
    return await create_start_link(bot, payload, encode=True)


def parse_fsm_payload(args: str) -> dict | None:
    """Parse FSM payload from deep link.

    Args:
        args: Encoded payload from /start command

    Returns:
        Dict with {command, group_id, task_id?} or None if invalid
    """
    try:
        payload = decode_payload(args)
        parts = payload.split("_")
        if len(parts) >= 2 and parts[0] in FSM_COMMANDS:
            result = {"command": parts[0], "group_id": int(parts[1])}
            if len(parts) == 3:
                result["task_id"] = int(parts[2])
            return result
    except Exception:
        pass
    return None
