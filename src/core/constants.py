# src/core/constants.py
"""Application constants and message templates."""

# Bot Info
BOT_NAME = "Task Automation Bot"
BOT_VERSION = "1.0.0"

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

# Timeouts (seconds)
FSM_TIMEOUT = 300  # 5 minutes
API_TIMEOUT = 30

# Message Templates
MSG_WELCOME = """*{bot_name}*

Commands:
/tasks - View tasks
/add - Create task
/remind - Set reminder
/help - All commands

Type /add to get started!"""

MSG_HELP = """*Available Commands*

*Task Management:*
/tasks - List all tasks
/add - Create new task
/delete - Remove task

*Reminders:*
/remind - Set reminder

*General:*
/start - Welcome message
/help - This help text
/status - Bot status
/settings - User preferences"""

MSG_TASK_CREATED = """Task created!

*Title:* {title}
*Due:* {due_date}
*ID:* `{task_id}`

Use /tasks to view all."""

MSG_ERROR = """Unable to process request.

*Reason:* {error}

Try again or use /help."""

MSG_CONFIRM_DELETE = """Delete task "{title}"?

This action cannot be undone."""

MSG_NO_TASKS = "No tasks found. Use /add to create one."
MSG_UNAUTHORIZED = "You don't have permission."
MSG_RATE_LIMITED = "Please wait before sending another request."
