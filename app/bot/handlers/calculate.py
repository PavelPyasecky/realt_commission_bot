from aiogram import F, Router
from aiogram.types import Message

from app.services import exceptions
from app.services.commission import CommissionCalculator
from app.i18n import get_translator


router = Router()


@router.message(F.text.regexp(r"^\d+$"))
async def calculate(message):
    _ = get_translator()
    try:
        calculator = await CommissionCalculator.from_query(message.text)
    except exceptions.InputError:
        await message.answer(_("Please enter a number in USD."))
        return
    except exceptions.CurrencyUnavailableError:
        await message.answer(
            _("USD rate is temporarily unavailable. Please try again in a minute.")
        )
        return
    await message.answer(calculator.format_html())


@router.message(F.text)
async def invalid_text(message):
    _ = get_translator()
    await message.answer(_("Please enter a number in USD."))
