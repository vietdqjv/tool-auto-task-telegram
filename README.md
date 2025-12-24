# Telegram Bot Automation Tool

Multi-purpose Python Telegram bot with task scheduling, reminders, and database persistence.

## Features

- **Task Management**: Create, view, complete, and delete tasks via Telegram
- **Reminders**: Schedule task reminders with APScheduler
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
| `/tasks` | View your tasks |
| `/add` | Create new task (3-step FSM) |
| `/status` | Bot status + task stats |
| `/settings` | User preferences |

## Project Structure

```
src/
├── main.py              # Entry point
├── core/                # Config, constants, exceptions
├── database/            # Models, repositories, engine
├── services/            # Business logic
├── scheduler/           # APScheduler jobs
└── bot/                 # Handlers, middlewares, keyboards
docker/
├── Dockerfile
└── docker-compose.yml
alembic/                 # Database migrations
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
