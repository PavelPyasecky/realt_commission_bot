import asyncio
import logging
from datetime import datetime, timezone

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.core.config import config
from app.infrastructure.database.transaction import managed_session
from app.infrastructure.repositories.announcement_repository import AnnouncementRepository
from app.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
_lock = asyncio.Lock()
_USER_PAGE = 50


async def _send_to_all_users(bot, sessionmaker, body_html: str) -> None:
    user_repo = UserRepository()
    offset = 0
    while True:
        async with managed_session(sessionmaker) as session:
            ids = await user_repo.list_tg_ids_batch(session, limit=_USER_PAGE, offset=offset)
        if not ids:
            break
        for tg_id in ids:
            try:
                await bot.send_message(tg_id, body_html, parse_mode=ParseMode.HTML)
            except TelegramForbiddenError:
                pass
            except TelegramBadRequest as exc:
                logger.debug("Skip user %s: %s", tg_id, exc)
            except Exception:
                logger.exception("Failed to send announcement to user %s", tg_id)
            await asyncio.sleep(config.ANNOUNCEMENT_SEND_DELAY_SECONDS)
        offset += len(ids)


async def deliver_due_announcements(bot, sessionmaker, *, batch_limit: int) -> None:
    if batch_limit <= 0:
        return
    async with _lock:
        repo = AnnouncementRepository()
        now = datetime.now(timezone.utc)
        async with managed_session(sessionmaker) as session:
            due = await repo.list_due(session, now=now, limit=batch_limit)
        for item in due:
            try:
                await _send_to_all_users(bot, sessionmaker, item.body_html)
            except Exception:
                logger.exception("Announcement id=%s broadcast failed", item.id)
                continue
            async with managed_session(sessionmaker) as session:
                await repo.mark_sent(session, item.id)


async def announcement_delivery_loop(bot, sessionmaker, interval_seconds: float, batch_limit: int) -> None:
    while True:
        try:
            await deliver_due_announcements(bot, sessionmaker, batch_limit=batch_limit)
        except Exception:
            logger.exception("Announcement delivery tick failed")
        await asyncio.sleep(interval_seconds)
