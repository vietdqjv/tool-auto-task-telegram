# src/bot/app.py
"""Bot and Dispatcher initialization."""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.core.config import settings
from src.database import async_session_factory


def create_bot() -> Bot:
    """Create and configure bot instance."""
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )


def create_dispatcher() -> Dispatcher:
    """Create dispatcher with routers and middlewares."""
    from src.bot.handlers import commands_router, tasks_router, callbacks_router, group_tasks_router
    from src.bot.middlewares import AuthMiddleware, RateLimitMiddleware

    # Use RedisStorage for FSM state persistence
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    # Register middlewares (outer = runs first)
    dp.message.outer_middleware(RateLimitMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register routers
    dp.include_router(commands_router)
    dp.include_router(tasks_router)
    dp.include_router(group_tasks_router)
    dp.include_router(callbacks_router)

    return dp


async def on_startup(bot: Bot):
    """Startup hook."""
    from loguru import logger
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


async def on_shutdown(bot: Bot):
    """Shutdown hook."""
    from loguru import logger
    logger.info("Bot shutting down...")


def get_session():
    """Get async session for handlers."""
    return async_session_factory()
