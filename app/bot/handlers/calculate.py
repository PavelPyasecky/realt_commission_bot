from aiogram import F, Router
from aiogram.types import Message

from app.services import exceptions
from app.services.commission import CommissionCalculator


router = Router()


@router.message(F.text.regexp(r"^\d+$"))
async def calculate(message):
    try:
        calculator = await CommissionCalculator.from_query(message.text)
    except exceptions.InputError:
        await message.answer("Please type a cost number of the object in USD: ")
        return
    await message.answer(calculator.format_html())


@router.message(F.text)
async def invalid_text(message):
    await message.answer("Please type a cost number of the object in USD: ")
