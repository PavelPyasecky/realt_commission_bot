from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.i18n import get_translator


router = Router()


@router.message(CommandStart())
async def start(message):
    _ = get_translator()
    await message.answer(
        _("Please enter the property price in USD.")
    )
