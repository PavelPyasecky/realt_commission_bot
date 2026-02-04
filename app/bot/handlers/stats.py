from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import config
from app.services.stats import StatsService


router = Router()


@router.message(Command("stats"))
async def stats(message, sessionmaker):
    if message.chat.id != config.ADMIN_CHAT_ID:
        await message.answer("Access denied.")
        return

    async with sessionmaker() as session:
        stats_data = await StatsService().get_stats(session)

    text = (
        f"DAU: {stats_data['dau']}\n"
        f"WAU: {stats_data['wau']}\n"
        f"MAU: {stats_data['mau']}\n"
        f"All unique: {stats_data['total']}\n"
    )
    await message.answer(text)
