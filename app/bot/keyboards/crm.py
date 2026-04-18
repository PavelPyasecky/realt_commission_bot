from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def build_crm_menu_keyboard(_=None):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Add lead") if _ else "Добавить лид"),
                KeyboardButton(text=_("Today leads") if _ else "Лиды на сегодня"),
            ],
            [
                KeyboardButton(text=_("All leads") if _ else "Все лиды"),
                KeyboardButton(text=_("Archived leads") if _ else "Архив лидов"),
            ],
            [KeyboardButton(text=_("Forwarded lead") if _ else "Лид из пересланного")],
            [KeyboardButton(text=_("Calculate commission") if _ else "Calculate commission")],
        ],
        resize_keyboard=True,
    )


def build_lead_card_keyboard(lead_id, archived=False, include_add_phone=False, _=None):
    rows = [
        [
            InlineKeyboardButton(
                text=_("Lead set reminder") if _ else "Напоминание",
                callback_data=f"lead:rem:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead change status") if _ else "Статус",
                callback_data=f"lead:status:{lead_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_("Lead mark called") if _ else "Отмечен звонок",
                callback_data=f"lead:call:{lead_id}",
            ),
            InlineKeyboardButton(
                text=_("Lead edit") if _ else "Изменить",
                callback_data=f"lead:edit:{lead_id}",
            ),
        ],
    ]
    if include_add_phone:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_("Lead phone") if _ else "Добавить телефон",
                    callback_data=f"edit:phone:{lead_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=_("Lead restore") if _ else "Восстановить",
                callback_data=f"lead:restore:{lead_id}",
            )
            if archived
            else InlineKeyboardButton(
                text=_("Lead archive") if _ else "В архив",
                callback_data=f"lead:archive:{lead_id}",
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_lead_list_keyboard(leads, _=None):
    rows = [[InlineKeyboardButton(text=lead.name[:32], callback_data=f"lead:open:{lead.id}")] for lead in leads]
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
                InlineKeyboardButton(text=_("Lead phone") if _ else "Телефон", callback_data=f"edit:phone:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead type") if _ else "Тип", callback_data=f"edit:type:{lead_id}"),
                InlineKeyboardButton(text=_("Lead source") if _ else "Источник", callback_data=f"edit:source:{lead_id}"),
            ],
            [
                InlineKeyboardButton(text=_("Lead status") if _ else "Статус", callback_data=f"edit:status:{lead_id}"),
                InlineKeyboardButton(text=_("Lead reminder") if _ else "Напоминание", callback_data=f"edit:rem:{lead_id}"),
            ],
            [InlineKeyboardButton(text=_("Back") if _ else "Назад", callback_data=f"lead:open:{lead_id}")],
        ]
    )


def build_duplicate_keyboard(existing_lead_id, _=None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Open existing") if _ else "Открыть существующий", callback_data=f"dup:open:{existing_lead_id}")],
            [InlineKeyboardButton(text=_("Create anyway") if _ else "Создать все равно", callback_data="dup:create")],
            [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
        ]
    )


def build_skip_phone_keyboard(edit_mode=False, lead_id=None, _=None):
    if edit_mode and lead_id is not None:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_("Skip") if _ else "Пропустить", callback_data=f"edit:phoneclear:{lead_id}")],
                [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("Skip") if _ else "Пропустить", callback_data="create:phone:skip")],
            [InlineKeyboardButton(text=_("CRM") if _ else "CRM", callback_data="crm:menu")],
        ]
    )
