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

    @property
    def jobstore_url(self) -> str:
        """Return job store URL, fallback to DATABASE_URL."""
        return self.SCHEDULER_JOBSTORE_URL or self.DATABASE_URL.replace("+aiosqlite", "")


settings = Settings()
