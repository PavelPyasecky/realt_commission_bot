import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Final

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import app.core.config as config_module


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

logger: Final = logging.getLogger(__name__)


class ApplicationContext:    
    def __init__(self) -> None:
        self.config = config_module.config
        self.bot = None
        self.dp: Dispatcher | None = None
    
    @property
    def db_dsn(self) -> str:
        return str(self.config.DB_DSN)


@asynccontextmanager
async def lifespan(app_ctx: ApplicationContext) -> ApplicationContext:
    logger.info("Starting Realtor Tax Bot...")
    
    app_ctx.bot = Bot(
        token=app_ctx.config.TELEGRAM_ACCESS_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    app_ctx.dp = Dispatcher(storage=MemoryStorage())
    
    logger.info(f"Connecting to DB: {app_ctx.db_dsn.split('@')[-1]}")
    logger.info(f"Base Value configured as: {app_ctx.config.BASIC_VALUE_BYN} BYN")
    
    yield app_ctx
    
    # Graceful shutdown
    if app_ctx.dp:
        await app_ctx.dp.stop_polling()
    if app_ctx.bot:
        await app_ctx.bot.session.close()
    logger.info("Bot stopped gracefully")


async def main() -> None:
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
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except SystemExit:
        logger.info("Bot stopped via system exit")
