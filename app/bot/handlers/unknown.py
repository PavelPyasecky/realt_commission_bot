from aiogram import Router
from aiogram.types import Message
from aiogram import F

from app.i18n import get_translator


router = Router()


@router.message(F.text.startswith("/"))
async def unknown(message):
    _ = get_translator()
    await message.answer(_("Sorry, I didn't understand that command."))
