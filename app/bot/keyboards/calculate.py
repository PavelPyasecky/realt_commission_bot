from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_main_keyboard(_, is_admin=False):
    keyboard = [
        [KeyboardButton(text=_("Calculate commission"))],
        [
            KeyboardButton(text=_("Last calculation")),
            KeyboardButton(text=_("Favorites")),
        ],
        [KeyboardButton(text=_("Compare scenarios"))],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text=_("User statistics"))])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def build_result_keyboard(_, amount_token, active_view="short"):
    short_selected = active_view == "short"
    detailed_selected = active_view == "detailed"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"• {_('Short')}" if short_selected else _("Short"),
                    callback_data=f"calc:noop:{amount_token}" if short_selected else f"calc:short:{amount_token}",
                ),
                InlineKeyboardButton(
                    text=f"• {_('Detailed')}" if detailed_selected else _("Detailed"),
                    callback_data=f"calc:noop:{amount_token}" if detailed_selected else f"calc:detailed:{amount_token}",
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

