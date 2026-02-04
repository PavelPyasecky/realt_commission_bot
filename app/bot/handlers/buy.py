from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


@router.message(Command("buy"))
async def buy(message):
    await message.answer("Payments are not available yet.")
