from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

from app.bot.keyboards import build_crm_menu_keyboard, build_main_keyboard
from app.bot.keyboards.crm import (
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
from app.core.config import config
from app.i18n import get_translator
from app.services.crm_options import LEAD_TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS
from app.services.leads import ForwardedLeadDraft, LeadService

router = Router()
lead_service = LeadService()

CREATE_DRAFT_KEY = "crm_create_draft"
FORWARDED_DRAFT_KEY = "crm_forwarded_draft"


class CRMFlow(StatesGroup):
    create_type = State()
    create_source = State()
    create_name = State()
    create_phone = State()
    create_reminder = State()
    edit_name = State()
    edit_phone = State()


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _is_admin(message: Message) -> bool:
    return (
        (message.chat and message.chat.id in config.ADMIN_ID)
        or (message.from_user and message.from_user.id in config.ADMIN_ID)
    )


def _is_crm_menu_text(text: str, _) -> bool:
    return text in {
        _("CRM"),
        _("Add lead"),
        _("Today leads"),
        _("All leads"),
        _("Archived leads"),
        _("Forwarded lead"),
        _("Back to main menu"),
    }


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


async def _show_crm_root(message: Message, state: FSMContext, _) -> None:
    await state.clear()
    await message.answer(_("CRM"), reply_markup=build_crm_menu_keyboard(_))


async def _show_lead_card(message: Message, lead, _) -> None:
    await message.answer(
        _format_lead_card(lead),
        reply_markup=build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_),
    )


async def _edit_or_answer(callback: CallbackQuery, text: str, reply_markup) -> None:
    if callback.message:
        if isinstance(reply_markup, InlineKeyboardMarkup):
            await callback.message.edit_text(text, reply_markup=reply_markup)
        else:
            await callback.message.answer(text, reply_markup=reply_markup)
    await callback.answer()


@router.message(Command("crm"))
async def crm_root(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    await _show_crm_root(message, state, _)


@router.message(F.text)
async def crm_menu_buttons(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    text = (message.text or "").strip()

    if not _is_crm_menu_text(text, _):
        return

    if text == _("CRM"):
        await _show_crm_root(message, state, _)
        return

    if text == _("Back to main menu"):
        await state.clear()
        await message.answer(_("Welcome message"), reply_markup=build_main_keyboard(_, is_admin=_is_admin(message)))
        return

    if text == _("Add lead"):
        await state.update_data(**{CREATE_DRAFT_KEY: {}})
        await state.set_state(CRMFlow.create_type)
        await message.answer(_("Choose lead type."), reply_markup=build_lead_type_keyboard("create:type", _=_))
        return

    if text == _("All leads"):
        async with sessionmaker() as session:
            leads = await lead_service.list_leads(session, message.from_user.id, archived=False)
        if not leads:
            await message.answer(_("No active leads yet."), reply_markup=build_crm_menu_keyboard(_))
            return
        lines = [
            f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for index, lead in enumerate(leads, start=1)
        ]
        await message.answer(_("All leads") + "\n\n" + "\n".join(lines), reply_markup=build_lead_list_keyboard(leads, _=_))
        return

    if text == _("Archived leads"):
        async with sessionmaker() as session:
            leads = await lead_service.list_leads(session, message.from_user.id, archived=True)
        if not leads:
            await message.answer(_("No archived leads."), reply_markup=build_crm_menu_keyboard(_))
            return
        lines = [
            f"{index}. {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
            for index, lead in enumerate(leads, start=1)
        ]
        await message.answer(_("Archived leads") + "\n\n" + "\n".join(lines), reply_markup=build_lead_list_keyboard(leads, archived=True, _=_))
        return

    if text == _("Today leads"):
        async with sessionmaker() as session:
            overdue, today = await lead_service.list_today(session, message.from_user.id)
        if not overdue and not today:
            await message.answer(_("No reminders for today."), reply_markup=build_crm_menu_keyboard(_))
            return
        sections = []
        if overdue:
            sections.append(_("Overdue"))
            sections.extend(
                f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
                for lead in overdue
            )
        if today:
            if sections:
                sections.append("")
            sections.append(_("Today"))
            sections.extend(
                f"- {lead.name} - {STATUS_LABELS.get(lead.status, lead.status)} - {_format_dt(lead.next_call_at)}"
                for lead in today
            )
        await message.answer("\n".join(sections), reply_markup=build_lead_list_keyboard(overdue + today, _=_))
        return

    if text == _("Forwarded lead"):
        await message.answer(_("Forward a client message to create a lead."), reply_markup=build_crm_menu_keyboard(_))
        return


@router.message(F.forward_origin.as_("forward_origin"))
async def forwarded_to_lead(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    if not message.from_user:
        return

    origin = message.forward_origin
    fallback_name = f"Telegram Lead {int(datetime.utcnow().timestamp())}"

    if hasattr(origin, "sender_user") and origin.sender_user:
        user = origin.sender_user
        display_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        draft = ForwardedLeadDraft(
            name=display_name or user.username or fallback_name,
            telegram_user_id=user.id,
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
            owner_user_id=message.from_user.id,
            telegram_user_id=str(draft.telegram_user_id) if draft.telegram_user_id is not None else None,
            telegram_username=draft.telegram_username,
            name=draft.name,
            source="telegram",
        )
        if duplicate:
            await state.update_data(**{FORWARDED_DRAFT_KEY: asdict(draft)})
            await message.answer(
                _("Possible duplicate found: {name}").format(name=duplicate.name),
                reply_markup=build_duplicate_keyboard(duplicate.id, _=_),
            )
            return

        lead = await lead_service.create_forwarded_lead(
            session,
            owner_user_id=message.from_user.id,
            owner_chat_id=message.chat.id,
            draft=draft,
        )
    await _show_lead_card(message, lead, _)


@router.callback_query(F.data == "crm:menu")
async def crm_menu(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    await state.clear()
    is_admin = (
        (callback.message and callback.message.chat and callback.message.chat.id in config.ADMIN_ID)
        or (callback.from_user and callback.from_user.id in config.ADMIN_ID)
    )
    await _edit_or_answer(callback, _("CRM"), build_main_keyboard(_, is_admin=is_admin))


@router.callback_query(F.data.startswith("create:type:"))
async def crm_add_type(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    value = callback.data.split(":")[2]
    data = await state.get_data()
    draft = dict(data.get(CREATE_DRAFT_KEY, {}))
    draft["lead_type"] = value
    await state.update_data(**{CREATE_DRAFT_KEY: draft})
    await state.set_state(CRMFlow.create_source)
    await _edit_or_answer(callback, _("Choose lead source."), build_source_keyboard("create:source", _=_))


@router.callback_query(F.data.startswith("create:source:"))
async def crm_add_source(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    value = callback.data.split(":")[2]
    data = await state.get_data()
    draft = dict(data.get(CREATE_DRAFT_KEY, {}))
    draft["source"] = value
    await state.update_data(**{CREATE_DRAFT_KEY: draft})
    await state.set_state(CRMFlow.create_name)
    await _edit_or_answer(callback, _("Send the lead name."), build_crm_menu_keyboard(_))


@router.callback_query(F.data == "create:phone:skip")
async def crm_skip_phone(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    data = await state.get_data()
    draft = dict(data.get(CREATE_DRAFT_KEY, {}))
    await state.update_data(**{CREATE_DRAFT_KEY: draft})
    await state.set_state(CRMFlow.create_reminder)
    await _edit_or_answer(callback, _("Choose the first reminder."), build_reminder_keyboard("create:rem", _=_))


@router.callback_query(F.data.startswith("create:rem:"))
async def crm_create_lead(callback: CallbackQuery, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    preset = callback.data.split(":")[2]
    draft = (await state.get_data()).get(CREATE_DRAFT_KEY, {})
    if not draft.get("name") or not draft.get("lead_type") or not draft.get("source"):
        await state.clear()
        await _edit_or_answer(callback, _("Lead draft expired. Start again from CRM."), build_crm_menu_keyboard(_))
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
            lead = await lead_service.set_reminder(
                session,
                callback.from_user.id,
                lead.id,
                lead_service.schedule_from_preset(preset),
            )
    await state.clear()
    await callback.message.answer(_format_lead_card(lead), reply_markup=build_lead_card_keyboard(lead.id, include_add_phone=lead.phone is None, _=_))
    await callback.answer()


@router.callback_query(F.data == "crm:list")
async def crm_list(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, callback.from_user.id, archived=False)
    if not leads:
        await _edit_or_answer(callback, _("No active leads yet."), build_crm_menu_keyboard(_))
        return
    lines = [
        f"{index}. {lead.name} - {lead.status_label} - {_format_dt(lead.next_call_at)}"
        for index, lead in enumerate(leads, start=1)
    ]
    await _edit_or_answer(callback, _("All leads") + "\n\n" + "\n".join(lines), build_lead_list_keyboard(leads, _=_))


@router.callback_query(F.data == "crm:arch")
async def crm_archived(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    async with sessionmaker() as session:
        leads = await lead_service.list_leads(session, callback.from_user.id, archived=True)
    if not leads:
        await _edit_or_answer(callback, _("No archived leads."), build_crm_menu_keyboard(_))
        return
    lines = [
        f"{index}. {lead.name} - {lead.status_label} - {_format_dt(lead.next_call_at)}"
        for index, lead in enumerate(leads, start=1)
    ]
    await _edit_or_answer(callback, _("Archived leads") + "\n\n" + "\n".join(lines), build_lead_list_keyboard(leads, archived=True, _=_))


@router.callback_query(F.data == "crm:today")
async def crm_today(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    async with sessionmaker() as session:
        overdue, today = await lead_service.list_today(session, callback.from_user.id)
    if not overdue and not today:
        await _edit_or_answer(callback, _("No reminders for today."), build_crm_menu_keyboard(_))
        return
    sections = []
    if overdue:
        sections.append(_("Overdue"))
        sections.extend(f"- {lead.name} - {lead.status_label} - {_format_dt(lead.next_call_at)}" for lead in overdue)
    if today:
        if sections:
            sections.append("")
        sections.append(_("Today"))
        sections.extend(f"- {lead.name} - {lead.status_label} - {_format_dt(lead.next_call_at)}" for lead in today)
    await _edit_or_answer(callback, "\n".join(sections), build_lead_list_keyboard(overdue + today, _=_))


@router.callback_query(F.data.startswith("dup:open:"))
async def crm_dup_open(callback: CallbackQuery, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await state.clear()
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data == "dup:create")
async def crm_dup_create(callback: CallbackQuery, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    draft = (await state.get_data()).get(FORWARDED_DRAFT_KEY)
    if not draft:
        await _edit_or_answer(callback, _("CRM"), build_crm_menu_keyboard(_))
        return
    async with sessionmaker() as session:
        lead = await lead_service.create_forwarded_lead(
            session,
            owner_user_id=callback.from_user.id,
            owner_chat_id=callback.message.chat.id,
            draft=ForwardedLeadDraft(**draft),
        )
    await state.clear()
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:open:"))
async def crm_open_lead(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:archive:"))
async def crm_archive(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.archive(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=True, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:restore:"))
async def crm_restore(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.restore(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=False, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:call:"))
async def crm_mark_called(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.mark_called(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:edit:"))
async def crm_edit_menu(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _("Edit {name}").format(name=lead.name), build_edit_menu_keyboard(lead.id, _=_))


@router.callback_query(F.data.startswith("lead:status:"))
async def crm_status_menu(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _("Choose the new status."), build_status_keyboard(lead_id, _=_))


@router.callback_query(F.data.startswith("status:set:"))
async def crm_set_status(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    _, _, lead_id, status = callback.data.split(":")
    async with sessionmaker() as session:
        lead = await lead_service.update_status(session, callback.from_user.id, int(lead_id), status)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("lead:rem:"))
async def crm_reminder_menu(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        await lead_service.get_lead(session, callback.from_user.id, lead_id)
    await _edit_or_answer(callback, _("Choose the reminder time."), build_reminder_keyboard("lead:remset", lead_id, _=_))


@router.callback_query(F.data.startswith("lead:remset:"))
async def crm_set_reminder(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
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
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("edit:name:"))
async def crm_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    await state.update_data(edit_lead_id=lead_id)
    await state.set_state(CRMFlow.edit_name)
    await _edit_or_answer(callback, _("Send the new lead name."), build_crm_menu_keyboard(_))


@router.callback_query(F.data.startswith("edit:phoneclear:"))
async def crm_clear_phone(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    async with sessionmaker() as session:
        lead = await lead_service.update_phone(session, callback.from_user.id, lead_id, "")
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("edit:phone:"))
async def crm_edit_phone(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    lead_id = int(callback.data.split(":")[2])
    await state.update_data(edit_lead_id=lead_id)
    await state.set_state(CRMFlow.edit_phone)
    await _edit_or_answer(callback, _("Send the new phone number."), build_skip_phone_keyboard(edit_mode=True, lead_id=lead_id, _=_))


@router.callback_query(F.data.startswith("edit:type:"))
async def crm_edit_type(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    parts = callback.data.split(":")
    if len(parts) == 3:
        lead_id = int(parts[2])
        async with sessionmaker() as session:
            await lead_service.get_lead(session, callback.from_user.id, lead_id)
        await _edit_or_answer(callback, _("Choose the new lead type."), build_lead_type_keyboard("edit:type", lead_id, _=_))
        return

    lead_id = int(parts[2])
    value = parts[3]
    async with sessionmaker() as session:
        lead = await lead_service.update_lead_type(session, callback.from_user.id, lead_id, value)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("edit:source:"))
async def crm_edit_source(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    parts = callback.data.split(":")
    if len(parts) == 3:
        lead_id = int(parts[2])
        async with sessionmaker() as session:
            await lead_service.get_lead(session, callback.from_user.id, lead_id)
        await _edit_or_answer(callback, _("Choose the new lead source."), build_source_keyboard("edit:source", lead_id, _=_))
        return

    lead_id = int(parts[2])
    value = parts[3]
    async with sessionmaker() as session:
        lead = await lead_service.update_source(session, callback.from_user.id, lead_id, value)
    await _edit_or_answer(callback, _format_lead_card(lead), build_lead_card_keyboard(lead.id, archived=lead.is_archived, include_add_phone=lead.phone is None, _=_))


@router.callback_query(F.data.startswith("edit:status:"))
async def crm_edit_status(callback: CallbackQuery, sessionmaker) -> None:
    await crm_status_menu(callback, sessionmaker)


@router.callback_query(F.data.startswith("edit:rem:"))
async def crm_edit_rem(callback: CallbackQuery, sessionmaker) -> None:
    await crm_reminder_menu(callback, sessionmaker)


@router.message(CRMFlow.create_name)
async def crm_create_name(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    name = (message.text or "").strip()
    if not name:
        await message.answer(_("Name is required. Send the lead name."), reply_markup=build_crm_menu_keyboard(_))
        return
    draft = (await state.get_data()).get(CREATE_DRAFT_KEY, {})
    draft["name"] = name
    await state.update_data(**{CREATE_DRAFT_KEY: draft})
    await state.set_state(CRMFlow.create_phone)
    await message.answer(_("Send the phone number or skip this field."), reply_markup=build_skip_phone_keyboard(_=_))


@router.message(CRMFlow.create_phone)
async def crm_create_phone(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    draft = (await state.get_data()).get(CREATE_DRAFT_KEY, {})
    draft["phone"] = (message.text or "").strip()
    await state.update_data(**{CREATE_DRAFT_KEY: draft})
    await state.set_state(CRMFlow.create_reminder)
    await message.answer(_("Choose the first reminder."), reply_markup=build_reminder_keyboard("create:rem", _=_))


@router.message(CRMFlow.edit_name)
async def crm_apply_name(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    lead_id = (await state.get_data()).get("edit_lead_id")
    async with sessionmaker() as session:
        lead = await lead_service.update_name(session, message.from_user.id, lead_id, (message.text or "").strip())
    await state.clear()
    await _show_lead_card(message, lead, _)


@router.message(CRMFlow.edit_phone)
async def crm_apply_phone(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    lead_id = (await state.get_data()).get("edit_lead_id")
    async with sessionmaker() as session:
        lead = await lead_service.update_phone(session, message.from_user.id, lead_id, (message.text or "").strip())
    await state.clear()
    await _show_lead_card(message, lead, _)
