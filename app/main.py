import asyncio
import logging
import sys

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
import redis.asyncio as redis

import app.core.config as config_module
from app.bot.handlers import router as bot_router
from app.bot.middlewares.user_activity import UserActivityMiddleware
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import create_engine, create_sessionmaker
from app.tasks.currency import update_usd_rate
from app.tasks.reminder_delivery import reminder_delivery_loop
from aiogram.exceptions import TelegramNetworkError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)

logger = logging.getLogger(__name__)
STARTUP_RETRY_DELAY_SECONDS = 5
MAX_STARTUP_RETRIES = 5


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


async def _ensure_currency_cache(app_ctx: ApplicationContext) -> None:
    redis_client = redis.from_url(str(app_ctx.config.REDIS_URL))
    try:
        if await redis_client.get("currency:usd") is None:
            await asyncio.to_thread(update_usd_rate)
    finally:
        await redis_client.aclose()
        await redis_client.connection_pool.disconnect()


async def stack_startup(app_ctx: ApplicationContext) -> None:
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

    await _ensure_currency_cache(app_ctx)

    logger.info(f"Connecting to DB: {app_ctx.db_dsn.split('@')[-1]}")
    logger.info(f"Base Value configured as: {app_ctx.config.BASIC_VALUE_BYN} BYN")
    logger.info(f"Admin IDs configured as: {app_ctx.config.ADMIN_ID}")

    async with app_ctx.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def stack_shutdown(
    app_ctx: ApplicationContext,
    *,
    stop_polling: bool,
    close_bot_session: bool = True,
) -> None:
    if stop_polling and app_ctx.dp:
        try:
            await app_ctx.dp.stop_polling()
        except RuntimeError:
            logger.info("Polling was already stopped before shutdown cleanup.")
    if close_bot_session and app_ctx.bot:
        await app_ctx.bot.session.close()
    if app_ctx.engine:
        await app_ctx.engine.dispose()
    logger.info("Bot stopped gracefully")


async def _run_polling(app_ctx: ApplicationContext) -> None:
    reminder_task = None
    try:
        await stack_startup(app_ctx)
        cfg = app_ctx.config
        reminder_task = asyncio.create_task(
            reminder_delivery_loop(
                app_ctx.bot,
                app_ctx.sessionmaker,
                cfg.REMINDER_DELIVERY_INTERVAL_SECONDS,
                cfg.REMINDER_DELIVERY_BATCH,
            ),
            name="reminder_delivery",
        )
        logger.info("Bot started via polling")
        if not app_ctx.dp:
            raise RuntimeError("Dispatcher not initialized")
        for attempt in range(1, MAX_STARTUP_RETRIES + 1):
            try:
                await app_ctx.dp.start_polling(app_ctx.bot)
                break
            except TelegramNetworkError as error:
                if attempt == MAX_STARTUP_RETRIES:
                    raise
                logger.warning(
                    "Telegram network error during polling startup attempt %s/%s: %s",
                    attempt,
                    MAX_STARTUP_RETRIES,
                    error,
                )
                await asyncio.sleep(STARTUP_RETRY_DELAY_SECONDS)
    finally:
        if reminder_task:
            reminder_task.cancel()
            try:
                await reminder_task
            except asyncio.CancelledError:
                pass
        await stack_shutdown(app_ctx, stop_polling=True, close_bot_session=True)


def _webhook_path(cfg) -> str:
    p = (cfg.WEBHOOK_PATH or "/webhook").strip()
    return p if p.startswith("/") else f"/{p}"


async def _run_webhook(app_ctx: ApplicationContext) -> None:
    cfg = app_ctx.config
    public_url = cfg.webhook_public_url()
    if not public_url:
        raise RuntimeError(
            "BOT_MODE=webhook requires WEBHOOK_URL (full URL) or WEBHOOK_BASE_URL (origin) plus WEBHOOK_PATH."
        )

    handler = None
    runner = None
    site = None
    reminder_task = None
    try:
        await stack_startup(app_ctx)

        aiohttp_app = web.Application()
        path = _webhook_path(cfg)
        handler = SimpleRequestHandler(
            dispatcher=app_ctx.dp,
            bot=app_ctx.bot,
            handle_in_background=cfg.WEBHOOK_HANDLE_IN_BACKGROUND,
            secret_token=cfg.WEBHOOK_SECRET_TOKEN,
            sessionmaker=app_ctx.sessionmaker,
        )
        handler.register(aiohttp_app, path=path)

        runner = web.AppRunner(aiohttp_app)
        await runner.setup()
        site = web.TCPSite(runner, host=cfg.WEBHOOK_HOST, port=cfg.WEBHOOK_PORT)
        await site.start()

        await app_ctx.dp.emit_startup(
            bot=app_ctx.bot,
            dispatcher=app_ctx.dp,
            sessionmaker=app_ctx.sessionmaker,
        )

        logger.info("Setting Telegram webhook to %s", public_url)
        await app_ctx.bot.set_webhook(
            url=public_url,
            secret_token=cfg.WEBHOOK_SECRET_TOKEN,
            drop_pending_updates=cfg.WEBHOOK_DROP_PENDING_ON_SET,
        )

        reminder_task = asyncio.create_task(
            reminder_delivery_loop(
                app_ctx.bot,
                app_ctx.sessionmaker,
                cfg.REMINDER_DELIVERY_INTERVAL_SECONDS,
                cfg.REMINDER_DELIVERY_BATCH,
            ),
            name="reminder_delivery",
        )

        logger.info("Webhook server listening on %s:%s%s", cfg.WEBHOOK_HOST, cfg.WEBHOOK_PORT, path)
        await asyncio.Future()
    finally:
        if reminder_task:
            reminder_task.cancel()
            try:
                await reminder_task
            except asyncio.CancelledError:
                pass
        if cfg.WEBHOOK_DELETE_ON_SHUTDOWN and app_ctx.bot:
            try:
                await app_ctx.bot.delete_webhook(drop_pending_updates=False)
            except Exception:
                logger.exception("Failed to delete webhook on shutdown")
        if app_ctx.dp and app_ctx.bot:
            await app_ctx.dp.emit_shutdown(
                bot=app_ctx.bot,
                dispatcher=app_ctx.dp,
                sessionmaker=app_ctx.sessionmaker,
            )
        if handler:
            await handler.close()
        if site:
            await site.stop()
        if runner:
            await runner.cleanup()
        await stack_shutdown(app_ctx, stop_polling=False, close_bot_session=False)


async def main():
    app_ctx = ApplicationContext()
    mode = app_ctx.config.BOT_MODE

    try:
        if mode == "webhook":
            await _run_webhook(app_ctx)
        elif mode in ("polling", "poll", ""):
            await _run_polling(app_ctx)
        else:
            raise ValueError(f"Unknown BOT_MODE={mode!r}; use 'polling' or 'webhook'.")
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
