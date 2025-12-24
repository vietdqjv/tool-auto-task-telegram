# src/main.py
"""Application entry point."""
import asyncio
from loguru import logger

from src.core.config import settings
from src.database import init_db, close_db, async_session_factory
from src.bot import create_bot, create_dispatcher, on_startup, on_shutdown
from src.scheduler import get_scheduler, set_bot_instance


async def main():
    """Main application entry."""
    # Configure logging
    logger.add(
        "logs/bot_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )

    # Initialize database
    logger.info("Initializing database...")
    await init_db()

    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    # Setup scheduler
    scheduler = get_scheduler()
    scheduler.setup()
    set_bot_instance(bot, async_session_factory)
    scheduler.start()

    # Register lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        logger.info("Shutting down...")
        scheduler.shutdown()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
