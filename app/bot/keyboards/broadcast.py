from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def build_broadcast_reply_keyboard(_, main_keyboard: ReplyKeyboardMarkup) -> ReplyKeyboardMarkup:
    broadcast_rows = [
        [
            KeyboardButton(text=_("Broadcast list pending")),
            KeyboardButton(text=_("Broadcast list failed")),
        ],
        [
            KeyboardButton(text=_("Broadcast list sent")),
            KeyboardButton(text=_("Broadcast new")),
        ],
        [KeyboardButton(text=_("Broadcast home"))],
    ]
    return ReplyKeyboardMarkup(
        keyboard=broadcast_rows + main_keyboard.keyboard,
        resize_keyboard=True,
    )


def build_broadcast_list_inline(_, rows: list[tuple[int, str]], list_key: str, page: int, has_more: bool) -> InlineKeyboardMarkup:
    buttons = []
    for aid, title in rows:
        label = (title[:28] + "…") if len(title) > 29 else title
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"bc:v:{aid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="«", callback_data=f"bc:l{list_key}:{page - 1}"))
    if has_more:
        nav.append(InlineKeyboardButton(text="»", callback_data=f"bc:l{list_key}:{page + 1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_broadcast_detail_keyboard(_, announcement_id: int, state: str) -> InlineKeyboardMarkup:
    rows = []
    if state == "pending":
        rows.append(
            [
                InlineKeyboardButton(text=_("Broadcast edit time"), callback_data=f"bc:es:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast edit text"), callback_data=f"bc:eb:{announcement_id}"),
            ],
        )
        rows.append(
            [
                InlineKeyboardButton(text=_("Broadcast cancel"), callback_data=f"bc:cn:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast delete"), callback_data=f"bc:dl:{announcement_id}"),
            ],
        )
    elif state == "failed":
        rows.append(
            [
                InlineKeyboardButton(text=_("Broadcast edit time"), callback_data=f"bc:es:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast edit text"), callback_data=f"bc:eb:{announcement_id}"),
            ],
        )
        rows.append([InlineKeyboardButton(text=_("Broadcast delete"), callback_data=f"bc:dl:{announcement_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
