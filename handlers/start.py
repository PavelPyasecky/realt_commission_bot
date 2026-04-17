from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from keyboards.main_menu import main_menu_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Choose a mode. Calculator works from plain number messages. CRM is managed with buttons.",
        reply_markup=main_menu_keyboard(),
    )
