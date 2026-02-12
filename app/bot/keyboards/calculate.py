from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_main_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("Calculate commission"))],
            [
                KeyboardButton(text=_("Last calculation")),
                KeyboardButton(text=_("Favorites")),
            ],
            [KeyboardButton(text=_("Compare scenarios"))],
        ],
        resize_keyboard=True,
    )


def build_result_keyboard(_, amount_token):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("Short"),
                    callback_data=f"calc:short:{amount_token}",
                ),
                InlineKeyboardButton(
                    text=_("Detailed"),
                    callback_data=f"calc:detailed:{amount_token}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("Add to favorites"),
                    callback_data=f"calc:fav:{amount_token}",
                ),
                InlineKeyboardButton(
                    text=_("Compare"),
                    callback_data=f"calc:compare:{amount_token}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("Share"),
                    switch_inline_query=str(amount_token),
                ),
                InlineKeyboardButton(
                    text=_("New calculation"),
                    callback_data="calc:new",
                ),
            ],
        ]
    )

