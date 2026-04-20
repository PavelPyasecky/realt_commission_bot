from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_broadcast_home_keyboard(_) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Broadcast list pending"), callback_data="bc:lp:0")],
            [InlineKeyboardButton(text=_("Broadcast list failed"), callback_data="bc:lf:0")],
            [InlineKeyboardButton(text=_("Broadcast list sent"), callback_data="bc:ls:0")],
            [InlineKeyboardButton(text=_("Broadcast new"), callback_data="bc:add")],
            [InlineKeyboardButton(text=_("Broadcast close menu"), callback_data="bc:x")],
        ]
    )


def build_broadcast_list_keyboard(_, rows: list[tuple[int, str]], list_key: str, page: int, has_more: bool) -> InlineKeyboardMarkup:
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
    buttons.append([InlineKeyboardButton(text=_("Broadcast back home"), callback_data="bc:h")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_broadcast_detail_keyboard(_, announcement_id: int, state: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=_("Broadcast back home"), callback_data="bc:h")]]
    if state == "cancelled":
        return InlineKeyboardMarkup(inline_keyboard=rows)
    if state == "pending":
        rows.insert(
            0,
            [
                InlineKeyboardButton(text=_("Broadcast edit time"), callback_data=f"bc:es:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast edit text"), callback_data=f"bc:eb:{announcement_id}"),
            ],
        )
        rows.insert(
            1,
            [
                InlineKeyboardButton(text=_("Broadcast cancel"), callback_data=f"bc:cn:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast delete"), callback_data=f"bc:dl:{announcement_id}"),
            ],
        )
    elif state == "failed":
        rows.insert(
            0,
            [
                InlineKeyboardButton(text=_("Broadcast edit time"), callback_data=f"bc:es:{announcement_id}"),
                InlineKeyboardButton(text=_("Broadcast edit text"), callback_data=f"bc:eb:{announcement_id}"),
            ],
        )
        rows.insert(1, [InlineKeyboardButton(text=_("Broadcast delete"), callback_data=f"bc:dl:{announcement_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
