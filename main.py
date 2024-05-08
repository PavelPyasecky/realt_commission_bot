import logging
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, InlineQueryHandler

import exceptions
from services.commission import CommissionCalculator
from settings import ACCESS_TOKEN
from utils import round_number

GIF_URL = "https://i.pinimg.com/originals/d5/a7/55/d5a755aee7b8aeabc44258b9aa173ba5.gif"
THUMBNAIL_URL = "https://thumbs.dreamstime.com/b/icon-commission-coins-commission-267725653.jpg"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Hey! I'm a bot. Please type a cost number of the object in USD!")


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text_with_html = calculate_commission(update.message.text)
    except exceptions.InputError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Please type a cost number of the object in USD: ")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text_with_html, parse_mode=ParseMode.HTML)


async def inline_commission(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        ),
    ]

    await context.bot.answer_inline_query(update.inline_query.id, results)


def calculate_commission(query):
    commission = CommissionCalculator(query)
    text = (f"Object cost (USD):\t<b>{round_number(commission.object_cost_in_USD)}$</b>\n"
            f"USD rate:\t<b>{round_number(commission.USD_rate)}$</b>\n"
            f"Object cost (BYN):\t<b>{round_number(commission.object_cost_in_BYN)}</b>\n"
            f"Basic Value (BYN):\t<b>{round_number(commission.BASIC_VALUE_IN_BYN)}</b>\n"
            f"Object cost in Basic Value (BV):\t<b>{round_number(commission.object_cost_in_basic_value)}</b>\n"
            f"Tax cost (BYN):\t<b>{round_number(commission.tax_cost_in_BYN)}</b>\n"
            f"Tax cost (USD):\t<b>{round_number(commission.tax_cost_in_USD)}$</b>\n")

    return text


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main() -> None:
    application = ApplicationBuilder().token(ACCESS_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    calculate_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), calculate)
    application.add_handler(calculate_handler)

    inline_commission_handler = InlineQueryHandler(inline_commission)
    application.add_handler(inline_commission_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
