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
                    text=f"{page}/{total_pages}",
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


def build_crm_menu_keyboard(_=None):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Add lead") if _ else "Add lead"),
                KeyboardButton(text=_("Today leads") if _ else "Today leads"),
            ],
            [
                KeyboardButton(text=_("All leads") if _ else "All leads"),
                KeyboardButton(text=_("Archived leads") if _ else "Archived leads"),
            ],
            [KeyboardButton(text=_("Forwarded lead") if _ else "Forwarded lead")],
            [KeyboardButton(text=_("Calculate commission") if _ else "Calculate commission")],
        ],
        resize_keyboard=True,
    )


def build_lead_card_keyboard(lead_id, archived=False, include_add_phone=False, _=None):
    rows = [
        [
            InlineKeyboardButton(
                text=_("Lead set reminder") if _ else "Set reminder",
                callback_data=f"lead:rem:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead change status") if _ else "Change status",
                callback_data=f"lead:status:{lead_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("Lead mark called") if _ else "Mark called",
                callback_data=f"lead:call:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead edit") if _ else "Edit",
                callback_data=f"lead:edit:{lead_id}",
            ),
        ],
    ]
    if include_add_phone:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_("Lead phone") if _ else "Add phone",
                    callback_data=f"edit:phone:{lead_id}",
                )
            ]
        )
    if archived:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_("Lead restore") if _ else "Restore",
                    callback_data=f"lead:restore:{lead_id}",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_("Lead archive") if _ else "Archive",
                    callback_data=f"lead:archive:{lead_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_list_keyboard(leads, archived=False, _=None):
    rows = []
    for lead in leads:
        rows.append([InlineKeyboardButton(text=lead.name[:32], callback_data=f"lead:open:{lead.id}")])
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_type_keyboard(prefix="create:type", lead_id=None, _=None):
    from app.services.crm_options import LEAD_TYPE_LABELS

    rows = []
    for value, label in LEAD_TYPE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=label, callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_source_keyboard(prefix="create:source", lead_id=None, _=None):
    from app.services.crm_options import SOURCE_LABELS

    rows = []
    for value, label in SOURCE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=label, callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_status_keyboard(lead_id, _=None):
    from app.services.crm_options import STATUS_LABELS

    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"status:set:{lead_id}:{value}")]
        for value, label in STATUS_LABELS.items()
    ]
    rows.append([InlineKeyboardButton(text=_("Back") if _ else "Back", callback_data=f"lead:open:{lead_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_reminder_keyboard(prefix="create:rem", lead_id=None, _=None):
    from app.services.crm_options import REMINDER_PRESETS

    rows = []
    for value, label in REMINDER_PRESETS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=label, callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_edit_menu_keyboard(lead_id, _=None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("Lead name") if _ else "Name", callback_data=f"edit:name:{lead_id}"),
                InlineKeyboardButton(text=_("Lead phone") if _ else "Phone", callback_data=f"edit:phone:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead type") if _ else "Type", callback_data=f"edit:type:{lead_id}"),
                InlineKeyboardButton(text=_("Lead source") if _ else "Source", callback_data=f"edit:source:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead status") if _ else "Status", callback_data=f"edit:status:{lead_id}"),
                InlineKeyboardButton(text=_("Lead reminder") if _ else "Reminder", callback_data=f"edit:rem:{lead_id}"),
            ],
            [InlineKeyboardButton(text=_("Back") if _ else "Back", callback_data=f"lead:open:{lead_id}")],
        ]
    )


def build_duplicate_keyboard(existing_lead_id, _=None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Open existing") if _ else "Open existing", callback_data=f"dup:open:{existing_lead_id}")],
            [InlineKeyboardButton(text=_("Create anyway") if _ else "Create anyway", callback_data="dup:create")],
            [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
        ]
    )


def build_skip_phone_keyboard(edit_mode=False, lead_id=None, _=None):
    if edit_mode and lead_id is not None:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_("Skip") if _ else "Skip", callback_data=f"edit:phoneclear:{lead_id}")],
                [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Skip") if _ else "Skip", callback_data="create:phone:skip")],
            [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
        ]
    )

