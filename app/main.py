import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import redis.asyncio as redis

import app.core.config as config_module
from app.bot.handlers import router as bot_router
from app.bot.middlewares.user_activity import UserActivityMiddleware
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import create_engine, create_sessionmaker
from app.tasks.currency import update_usd_rate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

logger = logging.getLogger(__name__)


class ApplicationContext:
    def __init__(self):
        self.config = config_module.config
        self.bot = None
        self.dp = None
        self.engine = None
        self.sessionmaker = None
    
    @property
    def db_dsn(self):
        return str(self.config.DB_DSN)


@asynccontextmanager
async def lifespan(app_ctx):
    logger.info("Starting Realtor Tax Bot...")
    
    app_ctx.bot = Bot(
        token=app_ctx.config.TELEGRAM_ACCESS_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    app_ctx.dp = Dispatcher(storage=MemoryStorage())
    app_ctx.engine = create_engine()
    app_ctx.sessionmaker = create_sessionmaker(app_ctx.engine)
    app_ctx.dp["sessionmaker"] = app_ctx.sessionmaker
    app_ctx.dp.include_router(bot_router)
    app_ctx.dp.update.middleware(UserActivityMiddleware())
    redis_client = redis.from_url(str(app_ctx.config.REDIS_URL))
    try:
        if await redis_client.get("currency:usd") is None:
            await asyncio.to_thread(update_usd_rate)
    finally:
        await redis_client.close()
        await redis_client.connection_pool.disconnect()
    
    logger.info(f"Connecting to DB: {app_ctx.db_dsn.split('@')[-1]}")
    logger.info(f"Base Value configured as: {app_ctx.config.BASIC_VALUE_BYN} BYN")
    logger.info(f"Admin IDs configured as: {app_ctx.config.ADMIN_ID}")

    async with app_ctx.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    
    yield app_ctx
    
    if app_ctx.dp:
        await app_ctx.dp.stop_polling()
    if app_ctx.bot:
        await app_ctx.bot.session.close()
    if app_ctx.engine:
        await app_ctx.engine.dispose()
    logger.info("Bot stopped gracefully")


async def main():
    app_ctx = ApplicationContext()
    
    try:
        async with lifespan(app_ctx):
            logger.info("Bot started via Polling!")
            if not app_ctx.dp:
                raise RuntimeError("Dispatcher not initialized")
            await app_ctx.dp.start_polling(app_ctx.bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped via KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Application finished")


if __name__ == "__main__":
    try:
        uvloop.install()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except SystemExit:
        logger.info("Bot stopped via system exit")
