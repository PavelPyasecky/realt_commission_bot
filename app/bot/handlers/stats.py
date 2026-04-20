from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import config
from app.infrastructure.database.transaction import managed_session
from app.services.stats import StatsService
from app.i18n import get_translator


router = Router()


@router.message(Command("stats"))
async def stats(message, sessionmaker):
    _ = get_translator()
    is_admin = (
        (message.chat and message.chat.id in config.ADMIN_ID)
        or (message.from_user and message.from_user.id in config.ADMIN_ID)
    )
    if not is_admin:
        await message.answer(_("Access denied."))
        return

    async with managed_session(sessionmaker) as session:
        stats_data = await StatsService().get_stats(session)

    text = (
        f"{_('Statistics')}\n\n"
        f"{_('Stats summary line dau').format(count=stats_data['dau'])}\n"
        f"{_('Stats summary line wau').format(count=stats_data['wau'])}\n"
        f"{_('Stats summary line mau').format(count=stats_data['mau'])}\n"
        f"{_('Stats summary line total').format(count=stats_data['total'])}\n"
    )
    await message.answer(text)
