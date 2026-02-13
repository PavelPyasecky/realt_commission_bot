from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards import build_main_keyboard
from app.core.config import config
from app.i18n import get_translator


router = Router()


@router.message(CommandStart())
async def start(message):
    _ = get_translator()
    is_admin = message.from_user and message.from_user.id in config.ADMIN_ID
    await message.answer(
        _("Welcome message"),
        reply_markup=build_main_keyboard(_, is_admin=is_admin),
    )
