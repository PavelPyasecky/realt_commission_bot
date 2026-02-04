from aiogram import Router
from aiogram.types import Message
from aiogram import F


router = Router()


@router.message(F.text.startswith("/"))
async def unknown(message):
    await message.answer("Sorry, I didn't understand that command.")
