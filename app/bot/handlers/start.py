from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router()


@router.message(CommandStart())
async def start(message):
    await message.answer(
        "Hey! I'm a bot. Please type a cost number of the object in USD!"
    )
