from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.i18n import get_translator


router = Router()


@router.message(Command("buy"))
async def buy(message):
    _ = get_translator()
    await message.answer(_("Payments are not available yet."))
