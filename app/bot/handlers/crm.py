from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.calculate import (
    build_crm_menu_keyboard,
    build_duplicate_keyboard,
    build_edit_menu_keyboard,
    build_lead_card_keyboard,
    build_lead_list_keyboard,
    build_lead_type_keyboard,
    build_reminder_keyboard,
    build_skip_phone_keyboard,
    build_source_keyboard,
    build_status_keyboard,
)
from app.services.crm_options import (
    LEAD_TYPE_LABELS,
    REMINDER_PRESETS,
    SOURCE_LABELS,
    STATUS_LABELS,
)
from app.services.leads import ForwardedLeadDraft, LeadService
from app.i18n import get_translator

router = Router()
lead_service = LeadService()

STATE_KEY = "crm_state"
CREATE_DRAFT_KEY = "crm_create_draft"
FORWARDED_DRAFT_KEY = "crm_forwarded_draft"


def _set_state(event, action: str, **payload) -> None:
    event.bot_data.setdefault(STATE_KEY, {})
    event.bot_data[STATE_KEY][event.from_user.id] = {"action": action, **payload}


def _get_state(event) -> dict:
    return event.bot_data.get(STATE_KEY, {}).get(event.from_user.id, {})


def _clear_state(event) -> None:
    event.bot_data.get(STATE_KEY, {}).pop(event.from_user.id, None)
    event.bot_data.get(CREATE_DRAFT_KEY, {}).pop(event.from_user.id, None)
    event.bot_data.get(FORWARDED_DRAFT_KEY, {}).pop(event.from_user.id, None)


def _draft_store(event, key: str) -> dict:
    event.bot_data.setdefault(key, {})
    event.bot_data[key].setdefault(event.from_user.id, {})
    return event.bot_data[key][event.from_user.id]


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _format_lead_card(lead) -> str:
    return (
        f"{lead.name}\n"
        f"Phone: {lead.phone or '-'}\n"
        f"Type: {LEAD_TYPE_LABELS.get(lead.lead_type, lead.lead_type)}\n"
        f"Source: {SOURCE_LABELS.get(lead.source, lead.source)}\n"
        f"Status: {STATUS_LABELS.get(lead.status, lead.status)}\n"
        f"Next call: {_format_dt(lead.next_call_at)}\n"
        f"Last contact: {_format_dt(lead.last_contact_at)}"
    )


async def _show_lead_card(target: Message | CallbackQuery, lead) -> None:
    text = _format_lead_card(lead)
    markup = build_lead_card_keyboard(
        lead.id,
        archived=lead.is_archived,
        include_add_phone=lead.phone is None,
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("crm"))
async def crm_root(message: Message) -> None:
    _clear_state(message)
    await message.answer("CRM", reply_markup=build_crm_menu_keyboard())


@router.message(F.text == "CRM")
async def crm_root_button(message: Message) -> None:
    await crm_root(message)


@router.message(F.text == "Add lead")
async def crm_add_button(message: Message) -> None:
    _draft_store(message, CREATE_DRAFT_KEY).clear()
    _set_state(message, "create_type")
    await message.answer("Choose lead type.", reply_markup=build_lead_type_keyboard("create:type"))


@router.message(F.text == "All leads")
async def crm_list_button(message: Message, sessionmaker) -> None:
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, message.from_user.id, archived=False)
    if not leads:
        await message.answer("No active leads yet.", reply_markup=build_crm_menu_keyboard())
        return
    lines = [
        f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
        for index, lead in enumerate(leads, start=1)
    ]
    await message.answer("All leads\n\n" + "\n".join(lines), reply_markup=build_lead_list_keyboard(leads))


@router.message(F.text == "Archived leads")
async def crm_archived_button(message: Message, sessionmaker) -> None:
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, message.from_user.id, archived=True)
    if not leads:
        await message.answer("No archived leads.", reply_markup=build_crm_menu_keyboard())
        return
    lines = [
        f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
        for index, lead in enumerate(leads, start=1)
    ]
    await message.answer("Archived leads\n\n" + "\n".join(lines), reply_markup=build_lead_list_keyboard(leads, archived=True))


@router.message(F.text == "Today leads")
async def crm_today_button(message: Message, sessionmaker) -> None:
    async with sessionmaker() as session:
        overdue, today = await lead_service.list_today(session, message.from_user.id)
    if not overdue and not today:
        await message.answer("No reminders for today.", reply_markup=build_crm_menu_keyboard())
        return
    sections = []
    if overdue:
        sections.append("Overdue")
        sections.extend(
            f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for lead in overdue
        )
    if today:
        if sections:
            sections.append("")
        sections.append("Today")
        sections.extend(
            f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for lead in today
        )
    await message.answer("\n".join(sections), reply_markup=build_lead_list_keyboard(overdue + today))


@router.message(F.text == "Forwarded lead")
async def crm_forward_hint(message: Message) -> None:
    await message.answer("Forward a client message to create a lead.", reply_markup=build_crm_menu_keyboard())


@router.message(F.forward_origin.as_("forward_origin"))
async def forwarded_to_lead(message: Message, sessionmaker) -> None:
    if not message.from_user:
        return

    owner_user_id = message.from_user.id
    owner_chat_id = message.chat.id
    origin = message.forward_origin
    fallback_name = f"Telegram Lead {int(datetime.utcnow().timestamp())}"

    if hasattr(origin, "sender_user") and origin.sender_user:
        user = origin.sender_user
        display_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        draft = ForwardedLeadDraft(
            name=display_name or user.username or fallback_name,
            telegram_user_id=str(user.id),
            telegram_username=user.username,
            telegram_display_name=display_name or user.username or fallback_name,
        )
    elif hasattr(origin, "sender_user_name") and origin.sender_user_name:
        draft = ForwardedLeadDraft(
            name=origin.sender_user_name,
            telegram_user_id=None,
            telegram_username=None,
            telegram_display_name=origin.sender_user_name,
        )
    else:
        draft = ForwardedLeadDraft(
            name=fallback_name,
            telegram_user_id=None,
            telegram_username=None,
            telegram_display_name=fallback_name,
        )

    async with sessionmaker() as session:
        duplicate = await lead_service.find_duplicate(
            session,
            owner_user_id=owner_user_id,
            telegram_user_id=draft.telegram_user_id,
            telegram_username=draft.telegram_username,
            name=draft.name,
            source="telegram",
        )
        if duplicate:
            _draft_store(message, FORWARDED_DRAFT_KEY).update(
                {
                    "name": draft.name,
                    "telegram_user_id": draft.telegram_user_id,
                    "telegram_username": draft.telegram_username,
                    "telegram_display_name": draft.telegram_display_name,
                }
            )
            await message.answer(
                f"Possible duplicate found: {duplicate.name}",
                reply_markup=build_duplicate_keyboard(duplicate.id),
            )
            return

        lead = await lead_service.create_forwarded_lead(
            session,
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            draft=draft,
        )
    await _show_lead_card(message, lead)


@router.callback_query(F.data == "crm:menu")
async def crm_menu(callback: CallbackQuery) -> None:
    _clear_state(callback)
    await callback.message.edit_text("CRM", reply_markup=build_crm_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "crm:add")
async def crm_add(callback: CallbackQuery) -> None:
    _draft_store(callback, CREATE_DRAFT_KEY).clear()
    _set_state(callback, "create_type")
    await callback.message.edit_text("Choose lead type.", reply_markup=build_lead_type_keyboard("create:type"))
    await callback.answer()


@router.callback_query(F.data.startswith("create:type:"))
async def crm_add_type(callback: CallbackQuery) -> None:
    value = callback.data.split(":")[2]
    _draft_store(callback, CREATE_DRAFT_KEY)["lead_type"] = value
    _set_state(callback, "create_source")
    await callback.message.edit_text("Choose lead source.", reply_markup=build_source_keyboard("create:source"))
    await callback.answer()


@router.callback_query(F.data.startswith("create:source:"))
async def crm_add_source(callback: CallbackQuery) -> None:
    value = callback.data.split(":")[2]
    _draft_store(callback, CREATE_DRAFT_KEY)["source"] = value
    _set_state(callback, "create_name")
    await callback.message.edit_text("Send the lead name.", reply_markup=build_crm_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "create:phone:skip")
async def crm_skip_phone(callback: CallbackQuery) -> None:
    _set_state(callback, "create_reminder")
    await callback.message.edit_text("Choose the first reminder.", reply_markup=build_reminder_keyboard("create:rem"))
    await callback.answer()


@router.callback_query(F.data.startswith("create:rem:"))
async def crm_create_lead(callback: CallbackQuery, sessionmaker) -> None:
    preset = callback.data.split(":")[2]
    draft = _draft_store(callback, CREATE_DRAFT_KEY)
    if not draft.get("name") or not draft.get("lead_type") or not draft.get("source"):
        _clear_state(callback)
        await callback.message.edit_text("Lead draft expired. Start again from CRM.", reply_markup=build_crm_menu_keyboard())
        await callback.answer()
        return

    async with sessionmaker() as session:
        lead = await lead_service.create_manual_lead(
            session,
            owner_user_id=callback.from_user.id,
            owner_chat_id=callback.message.chat.id,
            name=draft["name"],
            phone=draft.get("phone"),
            lead_type=draft["lead_type"],
            source=draft["source"],
        )
        if preset != "none":
            scheduled_at = lead_service.schedule_from_preset(preset)
            lead = await lead_service.set_reminder(session, callback.from_user.id, lead.id, scheduled_at)
    _clear_state(callback)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data == "crm:list")
async def crm_list(callback: CallbackQuery, sessionmaker) -> None:
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, callback.from_user.id, archived=False)
    if not leads:
        await callback.message.edit_text("No active leads yet.", reply_markup=build_crm_menu_keyboard())
    else:
        lines = [
            f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for index, lead in enumerate(leads, start=1)
        ]
        await callback.message.edit_text(
            "All leads\n\n" + "\n".join(lines),
            reply_markup=build_lead_list_keyboard(leads, archived=False),
        )
    await callback.answer()


@router.callback_query(F.data == "crm:arch")
async def crm_archived(callback: CallbackQuery, sessionmaker) -> None:
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, callback.from_user.id, archived=True)
    if not leads:
        await callback.message.edit_text("No archived leads.", reply_markup=build_crm_menu_keyboard())
    else:
        lines = [
            f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for index, lead in enumerate(leads, start=1)
        ]
        await callback.message.edit_text(
            "Archived leads\n\n" + "\n".join(lines),
            reply_markup=build_lead_list_keyboard(leads, archived=True),
        )
    await callback.answer()


@router.callback_query(F.data == "crm:today")
async def crm_today(callback: CallbackQuery, sessionmaker) -> None:
    async with sessionmaker() as session:
        overdue, today = await lead_service.list_today(session, callback.from_user.id)
    if not overdue and not today:
        await callback.message.edit_text("No reminders for today.", reply_markup=build_crm_menu_keyboard())
        await callback.answer()
        return

    sections = []
    if overdue:
        sections.append("Overdue")
        sections.extend(
            f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for lead in overdue
        )
    if today:
        if sections:
            sections.append("")
        sections.append("Today")
        sections.extend(
            f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for lead in today
        )
    await callback.message.edit_text("\n".join(sections), reply_markup=build_lead_list_keyboard(overdue + today))
    await callback.answer()


@router.callback_query(F.data.startswith("dup:open:"))
async def crm_dup_open(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    _clear_state(callback)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data == "dup:create")
async def crm_dup_create(callback: CallbackQuery, sessionmaker) -> None:
    draft = _draft_store(callback, FORWARDED_DRAFT_KEY)
    if not draft:
        await callback.message.edit_text("CRM", reply_markup=build_crm_menu_keyboard())
        await callback.answer()
        return
    async with sessionmaker() as session:
        lead = await lead_service.create_forwarded_lead(
            session,
            owner_user_id=callback.from_user.id,
            owner_chat_id=callback.message.chat.id,
            draft=ForwardedLeadDraft(**draft),
        )
    _clear_state(callback)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:open:"))
async def crm_open_lead(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:archive:"))
async def crm_archive(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.archive(session, callback.from_user.id, lead_id)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:restore:"))
async def crm_restore(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.restore(session, callback.from_user.id, lead_id)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:call:"))
async def crm_mark_called(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.mark_called(session, callback.from_user.id, lead_id)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:edit:"))
async def crm_edit_menu(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await callback.message.edit_text(f"Edit {lead.name}", reply_markup=build_edit_menu_keyboard(lead.id))
    await callback.answer()


@router.callback_query(F.data.startswith("lead:status:"))
async def crm_status_menu(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await callback.message.edit_text("Choose the new status.", reply_markup=build_status_keyboard(lead_id))
    await callback.answer()


@router.callback_query(F.data.startswith("status:set:"))
async def crm_set_status(callback: CallbackQuery, sessionmaker) -> None:
    _, _, lead_id, status = callback.data.split(":")
    async with sessionmaker() as session:
        lead = await lead_service.update_status(session, callback.from_user.id, int(lead_id), status)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("lead:rem:"))
async def crm_reminder_menu(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await callback.message.edit_text("Choose the reminder time.", reply_markup=build_reminder_keyboard("lead:remset", lead_id))
    await callback.answer()


@router.callback_query(F.data.startswith("lead:remset:"))
async def crm_set_reminder(callback: CallbackQuery, sessionmaker) -> None:
    _, _, lead_id, preset = callback.data.split(":")
    async with sessionmaker() as session:
        if preset == "none":
            lead = await lead_service.clear_reminder(session, callback.from_user.id, int(lead_id))
        else:
            lead = await lead_service.set_reminder(
                session,
                callback.from_user.id,
                int(lead_id),
                lead_service.schedule_from_preset(preset),
            )
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:name:"))
async def crm_edit_name(callback: CallbackQuery) -> None:
    lead_id = int(callback.data.split(":")[2])
    _set_state(callback, "edit_name", lead_id=lead_id)
    await callback.message.edit_text("Send the new lead name.", reply_markup=build_crm_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("edit:phoneclear:"))
async def crm_clear_phone(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.update_phone(session, callback.from_user.id, lead_id, "")
    _clear_state(callback)
    await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:phone:"))
async def crm_edit_phone(callback: CallbackQuery) -> None:
    lead_id = int(callback.data.split(":")[2])
    _set_state(callback, "edit_phone", lead_id=lead_id)
    await callback.message.edit_text("Send the new phone number.", reply_markup=build_skip_phone_keyboard(edit_mode=True, lead_id=lead_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit:type:"))
async def crm_edit_type(callback: CallbackQuery, sessionmaker) -> None:
    parts = callback.data.split(":")
    if len(parts) == 3:
        lead_id = int(parts[2])
        async with sessionmaker() as session:
            await lead_service.get_lead(session, callback.from_user.id, lead_id)
        await callback.message.edit_text("Choose the new lead type.", reply_markup=build_lead_type_keyboard("edit:type", lead_id))
    else:
        lead_id = int(parts[2])
        value = parts[3]
        async with sessionmaker() as session:
            lead = await lead_service.update_lead_type(session, callback.from_user.id, lead_id, value)
        await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:source:"))
async def crm_edit_source(callback: CallbackQuery, sessionmaker) -> None:
    parts = callback.data.split(":")
    if len(parts) == 3:
        lead_id = int(parts[2])
        async with sessionmaker() as session:
            await lead_service.get_lead(session, callback.from_user.id, lead_id)
        await callback.message.edit_text("Choose the new lead source.", reply_markup=build_source_keyboard("edit:source", lead_id))
    else:
        lead_id = int(parts[2])
        value = parts[3]
        async with sessionmaker() as session:
            lead = await lead_service.update_source(session, callback.from_user.id, lead_id, value)
        await _show_lead_card(callback, lead)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:status:"))
async def crm_edit_status(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await callback.message.edit_text("Choose the new status.", reply_markup=build_status_keyboard(lead_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit:rem:"))
async def crm_edit_rem(callback: CallbackQuery, sessionmaker) -> None:
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await callback.message.edit_text("Choose the reminder time.", reply_markup=build_reminder_keyboard("lead:remset", lead_id))
    await callback.answer()


@router.message(F.text)
async def crm_text_steps(message: Message, sessionmaker) -> None:
    state = _get_state(message)
    action = state.get("action")
    if not action:
        return

    if action == "create_name":
        name = (message.text or "").strip()
        if not name:
            await message.answer("Name is required. Send the lead name.", reply_markup=build_crm_menu_keyboard())
            return
        _draft_store(message, CREATE_DRAFT_KEY)["name"] = name
        _set_state(message, "create_phone")
        await message.answer("Send the phone number or skip this field.", reply_markup=build_skip_phone_keyboard())
        return

    if action == "create_phone":
        _draft_store(message, CREATE_DRAFT_KEY)["phone"] = (message.text or "").strip()
        _set_state(message, "create_reminder")
        await message.answer("Choose the first reminder.", reply_markup=build_reminder_keyboard("create:rem"))
        return

    if action == "edit_name":
        lead_id = state["lead_id"]
        async with sessionmaker() as session:
            lead = await lead_service.update_name(session, message.from_user.id, lead_id, (message.text or "").strip())
        _clear_state(message)
        await _show_lead_card(message, lead)
        return

    if action == "edit_phone":
        lead_id = state["lead_id"]
        async with sessionmaker() as session:
            lead = await lead_service.update_phone(session, message.from_user.id, lead_id, (message.text or "").strip())
        _clear_state(message)
        await _show_lead_card(message, lead)
