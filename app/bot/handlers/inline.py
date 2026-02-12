from uuid import uuid4

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from app.services import exceptions
from app.services.commission import CommissionCalculator
from app.services.rounding import round_fixed
from app.i18n import get_translator


router = Router()


@router.inline_query(F.query)
async def inline_commission(inline_query):
    try:
        calculator = await CommissionCalculator.from_query(inline_query.query)
    except exceptions.InputError:
        return

    _ = get_translator()
    description = (
        f"{_('Tax (USD):')} {round_fixed(calculator.tax_cost_in_USD)}$ | "
        f"{_('Commission rate:')} {round_fixed(calculator.commission)}%"
    )
    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title=_("Commission calculation"),
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=calculator.format_detailed_html(),
            parse_mode=ParseMode.HTML,
        ),
    )
    await inline_query.answer([result], cache_time=10)
