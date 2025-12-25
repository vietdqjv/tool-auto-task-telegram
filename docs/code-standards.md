# Code Standards - Telegram Bot Automation Tool

## Python Version
- Python 3.11+ required
- Use type hints throughout

## Project Structure
```
src/
├── main.py                    # Entry point
├── core/config.py             # Settings, constants, exceptions
├── database/
│   ├── models/                # SQLAlchemy models
│   └── repositories/          # Data access layer
├── services/                  # Business logic and external integrations
├── scheduler/                 # APScheduler setup and jobs
└── bot/                       # Telegram bot handlers, middlewares, keyboards
```

## Naming Conventions
- Files: `kebab-case.py` (e.g., `group-task-service.py`, `working-hours.py`)
- Modules/Packages: `snake_case` (e.g., `src.core`, `src.services`)
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## File Size
- Max 200 lines per file
- Split large modules into smaller components

## Async/Await
- Use `async/await` for I/O operations
- Prefer `asyncio` over threading

## Error Handling
```python
try:
    await operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

## Logging
- Use structured logging with `loguru`
- Log levels: DEBUG, INFO, WARNING, ERROR

## Configuration
- Use environment variables via `pydantic-settings`
- Never hardcode secrets

## Testing
- Use `pytest` with `pytest-asyncio`
- Aim for >80% coverage on core modules

## Dependencies
- Pin versions in `requirements.txt`
- Use `pip-tools` for dependency management

## Git Commits
- Conventional commits format
- Format: `type(scope): description`
