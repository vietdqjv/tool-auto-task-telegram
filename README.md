# Telegram Bot Automation Tool

Multi-purpose Python Telegram bot with task scheduling, reminders, and database persistence.

## Features

- **Personal Task Management**: Create, view, complete, and delete tasks via Telegram
- **Group Task Management**: Assign, remind, submit, verify, and reassign tasks within groups
- **Working Hours Enforcement**: Define specific working hours for task reminders
- **Recurring Reminders**: Automated reminders during work hours
- **Auto-Overdue Detection**: System automatically marks tasks as overdue
- **Completed Task Cleanup**: Automatically clean up completed tasks after a configurable period
- **FSM Conversations**: Multi-step task creation with state management
- **Rate Limiting**: Request throttling per user
- **Auto-registration**: Users registered on first message

## Tech Stack

| Component | Technology |
|-----------|------------|
| Bot Framework | aiogram 3.x |
| Scheduler | APScheduler 3.x |
| ORM | SQLAlchemy 2.x (async) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| FSM Storage | Redis |
| Config | pydantic-settings |

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example env
cp .env.example .env

# Edit .env with your values:
# - BOT_TOKEN from @BotFather
# - REDIS_URL (default: redis://localhost:6379/0)
```

### 3. Run Locally

```bash
# Start Redis (required for FSM)
docker run -d -p 6379:6379 redis:7-alpine

# Run bot
python -m src.main
```

## Docker Deployment

```bash
cd docker

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + menu |
| `/help` | List all commands |
| `/mytasks` | View your personal tasks |
| `/tasks` | View group tasks you are involved in |
| `/add` | Create new personal task (3-step FSM) |
| `/newtask` | Create new group task (multi-step FSM) |
| `/done <task_id>` | Mark a personal task as completed |
| `/submit <task_id>` | Submit a group task for verification |
| `/verify <task_id>` | Verify a submitted group task (admin/verifier only) |
| `/reject <task_id>` | Reject a submitted group task (admin/verifier only) |
| `/reassign <task_id> <user_id>` | Reassign a group task to another user (admin/verifier only) |
| `/status` | Bot status + task stats |
| `/settings` | User preferences |

## Project Structure

```
src/
├── main.py                    # Entry point
├── core/config.py             # Settings (working hours, timezone, reminder intervals)
├── database/
│   ├── models/task.py         # Task model with group task fields
│   ├── models/user.py         # User model
│   └── repositories/          # Data access layer
├── services/
│   ├── working-hours.py       # VN timezone working hours validation
│   ├── group-task-service.py  # Group task CRUD + workflow
│   ├── task-service.py        # Personal task service
│   └── notification.py        # Telegram notification service
├── scheduler/
│   ├── manager.py             # APScheduler singleton
│   └── jobs/
│       ├── notify.py          # Personal task reminders
│       └── group-task-reminder.py  # Group reminders, overdue, cleanup
└── bot/
    ├── handlers/
    │   ├── commands.py        # /start, /help, /status
    │   ├── tasks.py           # Personal task handlers
    │   ├── group-tasks.py     # Group task commands
    │   └── group-task-fsm.py  # Multi-step task creation
    ├── keyboards/
    │   ├── inline.py          # General keyboards
    │   └── group-task-keyboards.py  # Group task keyboards
    └── middlewares/           # Rate limiting, auth, session
```

## Development

```bash
# Run migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "Description"

# Syntax check
python3 -m py_compile src/**/*.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | required |
| `ADMIN_IDS` | Admin user IDs (JSON array) | `[]` |
| `DATABASE_URL` | Async database URL | `sqlite+aiosqlite:///./dev.db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `RATE_LIMIT_REQUESTS` | Max requests per period | `5` |
| `RATE_LIMIT_PERIOD` | Rate limit period (seconds) | `60` |

## License

MIT
