from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards import build_main_keyboard
from app.i18n import get_translator


router = Router()


@router.message(CommandStart())
async def start(message):
    _ = get_translator()
    await message.answer(
        _("Welcome message"),
        reply_markup=build_main_keyboard(_),
    )
