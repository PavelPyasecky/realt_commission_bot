from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models.crm_options import LEAD_TYPE_LABELS, REMINDER_PRESETS, SOURCE_LABELS, STATUS_LABELS


def crm_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Add Lead", callback_data="crm:add")],
            [InlineKeyboardButton("Add from Forwarded Message", callback_data="crm:fwd")],
            [
                InlineKeyboardButton("Today", callback_data="crm:today"),
                InlineKeyboardButton("All Leads", callback_data="crm:list"),
            ],
            [
                InlineKeyboardButton("Archived", callback_data="crm:arch"),
                InlineKeyboardButton("Main Menu", callback_data="menu:main"),
            ],
        ]
    )


def lead_card_keyboard(lead_id: int, *, archived: bool = False, include_add_phone: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("Set Reminder", callback_data=f"lead:rem:{lead_id}"),
            InlineKeyboardButton("Change Status", callback_data=f"lead:status:{lead_id}"),
        ],
        [
            InlineKeyboardButton("Mark Called", callback_data=f"lead:call:{lead_id}"),
            InlineKeyboardButton("Edit", callback_data=f"lead:edit:{lead_id}"),
        ],
    ]

    if include_add_phone:
        rows.append([InlineKeyboardButton("Add Phone", callback_data=f"edit:phone:{lead_id}")])

    if archived:
        rows.append([InlineKeyboardButton("Restore", callback_data=f"lead:restore:{lead_id}")])
    else:
        rows.append([InlineKeyboardButton("Archive", callback_data=f"lead:archive:{lead_id}")])

    rows.append([InlineKeyboardButton("Back to CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(rows)


def lead_list_keyboard(leads, *, archived: bool = False) -> InlineKeyboardMarkup:
    rows = []
    for lead in leads:
        label = lead.name[:32]
        rows.append([InlineKeyboardButton(label, callback_data=f"lead:open:{lead.id}")])

    rows.append([InlineKeyboardButton("Back", callback_data="crm:menu")])
    return InlineKeyboardMarkup(rows)


def lead_type_keyboard(prefix: str, lead_id: int | None = None) -> InlineKeyboardMarkup:
    rows = []
    for value, label in LEAD_TYPE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(label, callback_data=callback)])

    rows.append([InlineKeyboardButton("Cancel", callback_data="crm:menu")])
    return InlineKeyboardMarkup(rows)


def source_keyboard(prefix: str, lead_id: int | None = None) -> InlineKeyboardMarkup:
    rows = []
    for value, label in SOURCE_LABELS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(label, callback_data=callback)])

    rows.append([InlineKeyboardButton("Cancel", callback_data="crm:menu")])
    return InlineKeyboardMarkup(rows)


def status_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    rows = []
    for value, label in STATUS_LABELS.items():
        rows.append([InlineKeyboardButton(label, callback_data=f"status:set:{lead_id}:{value}")])

    rows.append([InlineKeyboardButton("Back", callback_data=f"lead:open:{lead_id}")])
    return InlineKeyboardMarkup(rows)


def reminder_keyboard(prefix: str, lead_id: int | None = None) -> InlineKeyboardMarkup:
    rows = []
    for value, label in REMINDER_PRESETS.items():
        callback = f"{prefix}:{value}" if lead_id is None else f"{prefix}:{lead_id}:{value}"
        rows.append([InlineKeyboardButton(label, callback_data=callback)])

    rows.append([InlineKeyboardButton("Cancel", callback_data="crm:menu")])
    return InlineKeyboardMarkup(rows)


def edit_menu_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Name", callback_data=f"edit:name:{lead_id}"),
                InlineKeyboardButton("Phone", callback_data=f"edit:phone:{lead_id}"),
            ],
            [
                InlineKeyboardButton("Type", callback_data=f"edit:type:{lead_id}"),
                InlineKeyboardButton("Source", callback_data=f"edit:source:{lead_id}"),
            ],
            [
                InlineKeyboardButton("Status", callback_data=f"edit:status:{lead_id}"),
                InlineKeyboardButton("Reminder", callback_data=f"edit:rem:{lead_id}"),
            ],
            [InlineKeyboardButton("Back", callback_data=f"lead:open:{lead_id}")],
        ]
    )


def duplicate_keyboard(existing_lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Open Existing", callback_data=f"dup:open:{existing_lead_id}")],
            [InlineKeyboardButton("Create Anyway", callback_data="dup:create")],
            [InlineKeyboardButton("Cancel", callback_data="crm:menu")],
        ]
    )


def skip_phone_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Skip", callback_data="create:phone:skip")],
            [InlineKeyboardButton("Cancel", callback_data="crm:menu")],
        ]
    )


def edit_phone_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Remove Phone", callback_data=f"edit:phoneclear:{lead_id}")],
            [InlineKeyboardButton("Set Phone", callback_data=f"edit:phone:{lead_id}")],
            [InlineKeyboardButton("Back", callback_data=f"lead:open:{lead_id}")],
        ]
    )


def reminder_notification_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Call Done", callback_data=f"rem:done:{lead_id}"),
                InlineKeyboardButton("+1 hour", callback_data=f"rem:snooze:{lead_id}:1h"),
            ],
            [
                InlineKeyboardButton("Tomorrow", callback_data=f"rem:snooze:{lead_id}:tm10"),
                InlineKeyboardButton("Change Status", callback_data=f"lead:status:{lead_id}"),
            ],
            [InlineKeyboardButton("Open Lead", callback_data=f"lead:open:{lead_id}")],
        ]
    )
