from __future__ import annotations

from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import exceptions
from services.commission import CommissionCalculator
from utils import round_number

THUMBNAIL_URL = "https://thumbs.dreamstime.com/b/icon-commission-coins-commission-267725653.jpg"


def calculate_commission(query: str) -> str:
    commission = CommissionCalculator(query)
    return (
        f"Object cost (USD):\t<b>{round_number(commission.object_cost_in_USD)}$</b>\n"
        f"USD rate:\t<b>{round_number(commission.USD_rate)}$</b>\n"
        f"Object cost (BYN):\t<b>{round_number(commission.object_cost_in_BYN)}</b>\n"
        f"Basic Value (BYN):\t<b>{round_number(commission.basic_value_in_BYN)}</b>\n"
        f"Object cost in Basic Value (BV):\t<b>{round_number(commission.object_cost_in_basic_value)}</b>\n"
        f"Commission (%):\t<b>{round_number(commission.commission)}%</b>\n"
        f"Tax cost (BYN):\t<b>{round_number(commission.tax_cost_in_BYN)}</b>\n"
        f"Tax cost (USD):\t<b>{round_number(commission.tax_cost_in_USD)}$</b>\n"
    )


async def send_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        text_with_html = calculate_commission(update.message.text)
    except exceptions.InputError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please type a cost number of the object in USD.",
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text_with_html,
        parse_mode=ParseMode.HTML,
    )


async def inline_commission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    text = calculate_commission(query)
    commission = CommissionCalculator(query)
    description = f"Tax cost (USD):\t{round_number(commission.tax_cost_in_USD)}$"
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Calculated commission",
            description=description,
            thumbnail_url=THUMBNAIL_URL,
            input_message_content=InputTextMessageContent(text, parse_mode=ParseMode.HTML),
        )
    ]

    await context.bot.answer_inline_query(update.inline_query.id, results)
