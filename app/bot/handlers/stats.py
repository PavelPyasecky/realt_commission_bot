from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import config
from app.services.stats import StatsService
from app.i18n import get_translator


router = Router()


@router.message(Command("stats"))
async def stats(message, sessionmaker):
    _ = get_translator()
    if message.chat.id not in config.ADMIN_ID:
        await message.answer(_("Access denied."))
        return

    async with sessionmaker() as session:
        stats_data = await StatsService().get_stats(session)

    text = (
        f"{_('Statistics')}\n\n"
        f"DAU — {_('Active in last 24 hours')}: {stats_data['dau']}\n"
        f"WAU — {_('Active in last 7 days')}: {stats_data['wau']}\n"
        f"MAU — {_('Active in last 30 days')}: {stats_data['mau']}\n"
        f"{_('All unique')}: {stats_data['total']}\n"
    )
    await message.answer(text)
