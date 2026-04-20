from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_crm_menu_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Add lead")),
                KeyboardButton(text=_("Today leads")),
            ],
            [
                KeyboardButton(text=_("All leads")),
                KeyboardButton(text=_("Archived leads")),
            ],
            [KeyboardButton(text=_("Forwarded lead"))],
            [
                KeyboardButton(text=_("Calculate commission")),
                KeyboardButton(text=_("Back to main menu")),
            ],
        ],
        resize_keyboard=True,
    )


def build_lead_card_keyboard(lead_id, archived=False, include_add_phone=False, _=None):
    rows = [
        [
            InlineKeyboardButton(
                text=_("Lead set reminder"),
                callback_data=f"lead:rem:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead change status"),
                callback_data=f"lead:status:{lead_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("Lead mark called"),
                callback_data=f"lead:call:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead edit"),
                callback_data=f"lead:edit:{lead_id}",
            ),
        ],
    ]
    if include_add_phone:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_("Lead phone"),
                    callback_data=f"edit:phone:{lead_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("Lead restore"),
                callback_data=f"lead:restore:{lead_id}",
            )
            if archived
            else InlineKeyboardButton(
                text=_("Lead archive"),
                callback_data=f"lead:archive:{lead_id}",
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_list_keyboard(leads, _=None):
    rows = [[InlineKeyboardButton(text=lead.name[:32], callback_data=f"lead:open:{lead.id}")] for lead in leads]
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_type_keyboard(prefix="create:type", lead_id=None, _=None):
    from app.services.crm_options import LEAD_TYPE_LABELS

    rows = []
    for value, label in LEAD_TYPE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_source_keyboard(prefix="create:source", lead_id=None, _=None):
    from app.services.crm_options import SOURCE_LABELS

    rows = []
    for value, label in SOURCE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_status_keyboard(lead_id, _=None):
    from app.services.crm_options import STATUS_LABELS

    rows = [
        [InlineKeyboardButton(text=_(label), callback_data=f"status:set:{lead_id}:{value}")]
        for value, label in STATUS_LABELS.items()
    ]
    rows.append([InlineKeyboardButton(text=_("Back"), callback_data=f"lead:open:{lead_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_reminder_keyboard(prefix="create:rem", lead_id=None, _=None):
    from app.services.crm_options import REMINDER_PRESETS

    rows = []
    for value, label in REMINDER_PRESETS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_edit_menu_keyboard(lead_id, _=None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("Lead name"), callback_data=f"edit:name:{lead_id}"),
                InlineKeyboardButton(text=_("Lead phone"), callback_data=f"edit:phone:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead type"), callback_data=f"edit:type:{lead_id}"),
                InlineKeyboardButton(text=_("Lead source"), callback_data=f"edit:source:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead status"), callback_data=f"edit:status:{lead_id}"),
                InlineKeyboardButton(text=_("Lead reminder"), callback_data=f"edit:rem:{lead_id}"),
            ],
            [InlineKeyboardButton(text=_("Back"), callback_data=f"lead:open:{lead_id}")],
        ]
    )


def build_duplicate_keyboard(existing_lead_id, _=None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Open existing"), callback_data=f"dup:open:{existing_lead_id}")],
            [InlineKeyboardButton(text=_("Create anyway"), callback_data="dup:create")],
            [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
        ]
    )


def build_skip_phone_keyboard(edit_mode=False, lead_id=None, _=None):
    if edit_mode and lead_id is not None:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_("Skip"), callback_data=f"edit:phoneclear:{lead_id}")],
                [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Skip"), callback_data="create:phone:skip")],
            [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
        ]
    )
