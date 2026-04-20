from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.callback_short import lead_id_to_b36, lead_open_callback, status_callback


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


def _lid(lead_id: int) -> str:
    return lead_id_to_b36(lead_id)


def build_lead_card_keyboard(lead_id, archived=False, include_add_phone=False, _=None):
    b = _lid(lead_id)
    rows = [
        [
            InlineKeyboardButton(text=_("Lead set reminder"), callback_data=f"r:{b}"),
            InlineKeyboardButton(text=_("Lead change status"), callback_data=f"z:{b}"),
        ],
        [
            InlineKeyboardButton(text=_("Lead mark called"), callback_data=f"k:{b}"),
            InlineKeyboardButton(text=_("Lead edit"), callback_data=f"e:{b}"),
        ],
    ]
    if include_add_phone:
        rows.append([InlineKeyboardButton(text=_("Lead phone"), callback_data=f"p:{b}")])
    rows.append(
        [
            InlineKeyboardButton(text=_("Lead restore"), callback_data=f"v:{b}")
            if archived
            else InlineKeyboardButton(text=_("Lead archive"), callback_data=f"a:{b}")
        ]
    )
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_list_keyboard(leads, archived=False, _=None):
    rows = [
        [InlineKeyboardButton(text=lead.name[:32], callback_data=lead_open_callback(lead.id))]
        for lead in leads
    ]
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_type_keyboard(prefix="create:type", lead_id=None, _=None):
    from app.services.crm_options import LEAD_TYPE_LABELS

    rows = []
    for value, label in LEAD_TYPE_LABELS.items():
        if lead_id is None:
            callback = f"ct:{value}"
        else:
            callback = f"yt:{_lid(lead_id)}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_source_keyboard(prefix="create:source", lead_id=None, _=None):
    from app.services.crm_options import SOURCE_LABELS

    rows = []
    for value, label in SOURCE_LABELS.items():
        if lead_id is None:
            callback = f"cf:{value}"
        else:
            callback = f"yf:{_lid(lead_id)}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_status_keyboard(lead_id, _=None):
    from app.services.crm_options import STATUS_LABELS

    b = _lid(lead_id)
    rows = [
        [InlineKeyboardButton(text=_(label), callback_data=status_callback(lead_id, value))]
        for value, label in STATUS_LABELS.items()
    ]
    rows.append([InlineKeyboardButton(text=_("Back"), callback_data=lead_open_callback(lead_id))])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_reminder_keyboard(prefix="create:rem", lead_id=None, _=None):
    from app.services.crm_options import REMINDER_PRESETS

    rows = []
    for value, label in REMINDER_PRESETS.items():
        if lead_id is None:
            callback = f"cq:{value}"
        else:
            callback = f"mq:{_lid(lead_id)}:{value}"
        rows.append([InlineKeyboardButton(text=_(label), callback_data=callback)])
    rows.append([InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_edit_menu_keyboard(lead_id, _=None):
    b = _lid(lead_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("Lead name"), callback_data=f"fn:{b}"),
                InlineKeyboardButton(text=_("Lead phone"), callback_data=f"fp:{b}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead type"), callback_data=f"ft:{b}"),
                InlineKeyboardButton(text=_("Lead source"), callback_data=f"fs:{b}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead status"), callback_data=f"fz:{b}"),
                InlineKeyboardButton(text=_("Lead reminder"), callback_data=f"fr:{b}"),
            ],
            [InlineKeyboardButton(text=_("Back"), callback_data=lead_open_callback(lead_id))],
        ]
    )


def build_duplicate_keyboard(existing_lead_id, _=None):
    b = _lid(existing_lead_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Open existing"), callback_data=f"do:{b}")],
            [InlineKeyboardButton(text=_("Create anyway"), callback_data="dx")],
            [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
        ]
    )


def build_skip_phone_keyboard(edit_mode=False, lead_id=None, _=None):
    if edit_mode and lead_id is not None:
        b = _lid(lead_id)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_("Skip"), callback_data=f"pc:{b}")],
                [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Skip"), callback_data="ps")],
            [InlineKeyboardButton(text=_("Back to CRM"), callback_data="crm:menu")],
        ]
    )
