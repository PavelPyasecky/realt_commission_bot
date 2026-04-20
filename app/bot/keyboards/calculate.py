from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_main_keyboard(_, is_admin=False):
    keyboard = [
        [
            KeyboardButton(text=_("Calculate commission")),
            KeyboardButton(text=_("CRM")),
        ],
        [
            KeyboardButton(text=_("Last calculation")),
            KeyboardButton(text=_("Favorites")),
        ],
        [KeyboardButton(text=_("Compare scenarios"))],
    ]
    if is_admin:
        keyboard.append(
            [
                KeyboardButton(text=_("User statistics")),
                KeyboardButton(text=_("Admin broadcast")),
            ]
        )
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


def build_user_stats_keyboard(_, period, page, total_pages):
    def _period_button(label_key, period_value):
        selected = period == period_value
        return InlineKeyboardButton(
            text=f"• {_(label_key)}" if selected else _(label_key),
            callback_data=(
                f"ustats:noop:{period}:{page}"
                if selected
                else f"ustats:period:{period_value}:1"
            ),
        )

    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    is_first = page <= 1
    is_last = page >= total_pages
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _period_button("Stats period day", "day"),
                _period_button("Stats period week", "week"),
                _period_button("Stats period month", "month"),
            ],
            [
                InlineKeyboardButton(
                    text=_("Stats previous"),
                    callback_data=(
                        f"ustats:noop:{period}:{page}"
                        if is_first
                        else f"ustats:page:{period}:{prev_page}"
                    ),
                ),
                InlineKeyboardButton(
                    text=_("Stats page counter").format(page=page, total=total_pages),
                    callback_data=f"ustats:noop:{period}:{page}",
                ),
                InlineKeyboardButton(
                    text=_("Stats next"),
                    callback_data=(
                        f"ustats:noop:{period}:{page}"
                        if is_last
                        else f"ustats:page:{period}:{next_page}"
                    ),
                ),
            ],
        ]
    )
