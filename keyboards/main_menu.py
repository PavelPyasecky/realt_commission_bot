from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Commission Calculator", callback_data="menu:calc")],
            [InlineKeyboardButton("CRM", callback_data="crm:menu")],
        ]
    )
