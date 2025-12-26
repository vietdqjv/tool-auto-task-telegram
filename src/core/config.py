# src/core/config.py
"""Application configuration via pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Bot configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot
    BOT_TOKEN: str = Field(..., description="Telegram Bot API token")
    ADMIN_IDS: list[int] = Field(default_factory=list, description="Admin user IDs")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Async database URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for FSM storage"
    )

    # Scheduler
    SCHEDULER_JOBSTORE_URL: str | None = Field(
        default=None,
        description="Job store DB URL (defaults to DATABASE_URL)"
    )

    # External API
    API_BASE_URL: str = Field(default="", description="External API base URL")
    API_KEY: str = Field(default="", description="External API key")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=5, description="Max requests per period")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="Rate limit period in seconds")

    # Working Hours (VN timezone with lunch break)
    TIMEZONE: str = Field(default="Asia/Ho_Chi_Minh", description="Timezone for working hours")
    WORKING_PERIODS: list[tuple[int, int, int, int]] = Field(
        default=[(8, 30, 12, 0), (13, 30, 17, 30)],
        description="Working periods as (start_h, start_m, end_h, end_m)"
    )
    WORKING_DAYS: list[int] = Field(
        default=[0, 1, 2, 3, 4],
        description="Working days (0=Mon, 6=Sun)"
    )
    MIN_REMINDER_INTERVAL: int = Field(
        default=15,
        description="Minimum reminder interval in minutes"
    )

    # Task cleanup
    COMPLETED_TASK_RETENTION_DAYS: int = Field(
        default=30,
        description="Days to keep completed tasks before cleanup"
    )

    @property
    def jobstore_url(self) -> str:
        """Return job store URL for APScheduler (sync driver required)."""
        if self.SCHEDULER_JOBSTORE_URL:
            return self.SCHEDULER_JOBSTORE_URL
        # Convert async URL to sync: asyncpg -> psycopg2, aiosqlite -> sqlite
        url = self.DATABASE_URL
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        url = url.replace("sqlite+aiosqlite://", "sqlite://")
        return url


settings = Settings()
