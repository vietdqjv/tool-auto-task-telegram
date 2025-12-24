# System Architecture - Telegram Bot Automation Tool

## Tech Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| **Bot Framework** | `aiogram 3.x` | Native async, FSM built-in, middleware, active dev, type hints |
| **Scheduler** | `APScheduler 3.x` | Async support, persistent jobs, cron/interval triggers |
| **Database** | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy abstracts both |
| **HTTP Client** | `httpx` | Modern async, HTTP/2, timeout handling |
| **ORM** | `SQLAlchemy 2.x + asyncpg` | Async-first, Alembic migrations |
| **Config** | `pydantic-settings` | Env validation, type coercion |
| **Container** | Docker + compose | Reproducible, easy orchestration |

## Project Structure

```
src/
├── bot/
│   ├── app.py              # Bot init, dispatcher
│   ├── handlers/
│   │   ├── commands.py     # /start, /help, /status
│   │   ├── tasks.py        # Task CRUD handlers
│   │   └── callbacks.py    # Inline button callbacks
│   ├── middlewares/
│   │   └── auth.py         # User auth middleware
│   └── keyboards/
│       └── inline.py       # Keyboard builders
├── scheduler/
│   ├── manager.py          # APScheduler setup
│   └── jobs/
│       └── notify.py       # Notification jobs
├── services/
│   ├── task_service.py     # Task business logic
│   ├── api_client.py       # External API wrapper
│   └── notification.py     # Notification service
├── database/
│   ├── engine.py           # Async engine, sessions
│   ├── models/
│   │   ├── user.py
│   │   └── task.py
│   └── repositories/
│       ├── user_repo.py
│       └── task_repo.py
├── core/
│   ├── config.py           # Pydantic settings
│   ├── constants.py
│   └── exceptions.py
└── main.py                 # Entry point
tests/
alembic/                    # Migrations
docker/
├── Dockerfile
└── docker-compose.yml
```

## Core Modules

| Module | Responsibility |
|--------|----------------|
| `bot/handlers` | Process commands/callbacks, delegate to services |
| `bot/middlewares` | Auth, rate limiting, logging |
| `scheduler/manager` | APScheduler with SQLAlchemy job store |
| `services/` | Business logic, external API calls |
| `database/repositories` | Data access, abstract DB queries |
| `core/config` | Env-based settings via pydantic |

## Configuration

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: list[int] = []
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    SCHEDULER_JOBSTORE_URL: str | None = None
    API_BASE_URL: str = ""
    API_KEY: str = ""
    class Config:
        env_file = ".env"
```

## Deployment (Docker)

```yaml
# docker-compose.yml
services:
  bot:
    build: .
    env_file: .env.prod
    depends_on: [db]
    restart: unless-stopped
  db:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: telegram_bot
      POSTGRES_USER: bot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
volumes:
  postgres_data:
```

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY alembic/ ./alembic/
CMD ["python", "-m", "src.main"]
```

## Data Flow

```
User -> Telegram -> aiogram Dispatcher -> Handlers -> Services -> Repos -> DB
APScheduler -> Jobs -> Services -> Bot API (notifications)
```

## Design Decisions

1. **Repository Pattern** - Isolate DB; swap without changing services
2. **Service Layer** - Thin handlers; reusable business logic
3. **Async Everything** - Non-blocking I/O for high concurrency
4. **Config via Env** - 12-factor app; same code across environments
5. **Files <200 Lines** - Single responsibility; easy testing

## Dependencies

```txt
# requirements.txt
aiogram>=3.4
APScheduler>=3.10
SQLAlchemy[asyncio]>=2.0
asyncpg
aiosqlite
httpx
pydantic-settings>=2.0
alembic
```
