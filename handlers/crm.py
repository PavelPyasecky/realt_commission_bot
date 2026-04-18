from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from keyboards.crm import (
    crm_menu_keyboard,
    duplicate_keyboard,
    edit_menu_keyboard,
    edit_phone_keyboard,
    lead_card_keyboard,
    lead_list_keyboard,
    lead_type_keyboard,
    reminder_keyboard,
    skip_phone_keyboard,
    source_keyboard,
    status_keyboard,
)
from keyboards.main_menu import main_menu_keyboard
from models.lead import Lead
from services.lead_service import ForwardedLeadDraft, LeadService
from services.reminder_service import ReminderService

STATE_KEY = "crm_state"
CREATE_DRAFT_KEY = "crm_create_draft"
FORWARDED_DRAFT_KEY = "crm_forwarded_draft"


class CRMHandler:
    def __init__(self, lead_service: LeadService, reminder_service: ReminderService):
        self.lead_service = lead_service
        self.reminder_service = reminder_service

    async def open_crm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self._reset_state(context)
        await self._reply(
            update,
            context,
            text="CRM",
            reply_markup=crm_menu_keyboard(),
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "menu:main":
            self._reset_state(context)
            await self._reply(update, context, "Main menu", main_menu_keyboard())
            return

        if data == "menu:calc":
            self._reset_state(context)
            await self._reply(
                update,
                context,
                "Send the property price in USD as a plain number. CRM remains available from the menu.",
                main_menu_keyboard(),
            )
            return

        if data == "crm:menu":
            await self.open_crm(update, context)
            return

        if data == "crm:add":
            context.user_data[CREATE_DRAFT_KEY] = {}
            self._set_state(context, "create_type")
            await self._reply(
                update,
                context,
                "Choose lead type.",
                lead_type_keyboard("create:type"),
            )
            return

        if data.startswith("create:type:"):
            context.user_data.setdefault(CREATE_DRAFT_KEY, {})["lead_type"] = data.split(":")[2]
            self._set_state(context, "create_source")
            await self._reply(
                update,
                context,
                "Choose lead source.",
                source_keyboard("create:source"),
            )
            return

        if data.startswith("create:source:"):
            context.user_data.setdefault(CREATE_DRAFT_KEY, {})["source"] = data.split(":")[2]
            self._set_state(context, "create_name")
            await self._reply(
                update,
                context,
                "Send the lead name.",
                crm_menu_keyboard(),
            )
            return

        if data == "create:phone:skip":
            await self._prompt_manual_reminder(update, context)
            return

        if data.startswith("create:rem:"):
            await self._complete_manual_creation(update, context, data.split(":")[2])
            return

        if data == "crm:fwd":
            self._set_state(context, "await_forwarded")
            context.user_data.pop(FORWARDED_DRAFT_KEY, None)
            await self._reply(
                update,
                context,
                "Forward a client message to create a lead.",
                crm_menu_keyboard(),
            )
            return

        if data == "crm:list":
            await self._show_lead_list(update, context, archived=False)
            return

        if data == "crm:arch":
            await self._show_lead_list(update, context, archived=True)
            return

        if data == "crm:today":
            await self._show_today(update, context)
            return

        if data.startswith("dup:open:"):
            self._reset_state(context)
            await self._show_lead_card(update, context, int(data.split(":")[2]))
            return

        if data == "dup:create":
            await self._create_forwarded_duplicate(update, context)
            return

        if data.startswith("lead:open:"):
            await self._show_lead_card(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:archive:"):
            await self._archive_lead(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:restore:"):
            await self._restore_lead(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:call:"):
            await self._mark_called(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:edit:"):
            await self._show_edit_menu(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:status:"):
            await self._show_status_menu(update, context, int(data.split(":")[2]))
            return

        if data.startswith("status:set:"):
            _, _, lead_id, status = data.split(":")
            await self._set_status(update, context, int(lead_id), status)
            return

        if data.startswith("lead:rem:"):
            await self._show_reminder_menu(update, context, int(data.split(":")[2]))
            return

        if data.startswith("lead:remset:"):
            _, _, lead_id, preset = data.split(":")
            await self._set_reminder(update, context, int(lead_id), preset)
            return

        if data.startswith("edit:name:"):
            self._set_state(context, "edit_name", lead_id=int(data.split(":")[2]))
            await self._reply(update, context, "Send the new lead name.", crm_menu_keyboard())
            return

        if data.startswith("edit:phoneclear:"):
            await self._clear_phone(update, context, int(data.split(":")[2]))
            return

        if data.startswith("edit:phone:"):
            self._set_state(context, "edit_phone", lead_id=int(data.split(":")[2]))
            await self._reply(
                update,
                context,
                "Send the new phone number.",
                edit_phone_keyboard(int(data.split(":")[2])),
            )
            return

        if data.startswith("edit:type:"):
            parts = data.split(":")
            if len(parts) == 3:
                await self._reply(
                    update,
                    context,
                    "Choose the new lead type.",
                    lead_type_keyboard("edit:type", int(parts[2])),
                )
                return
            await self._set_type(update, context, int(parts[2]), parts[3])
            return

        if data.startswith("edit:source:"):
            parts = data.split(":")
            if len(parts) == 3:
                await self._reply(
                    update,
                    context,
                    "Choose the new lead source.",
                    source_keyboard("edit:source", int(parts[2])),
                )
                return
            await self._set_source(update, context, int(parts[2]), parts[3])
            return

        if data.startswith("edit:status:"):
            await self._show_status_menu(update, context, int(data.split(":")[2]))
            return

        if data.startswith("edit:rem:"):
            await self._show_reminder_menu(update, context, int(data.split(":")[2]))
            return

        if data.startswith("rem:done:"):
            await self._mark_called(update, context, int(data.split(":")[2]))
            return

        if data.startswith("rem:snooze:"):
            _, _, lead_id, preset = data.split(":")
            await self._set_reminder(update, context, int(lead_id), preset)
            return

        await self._reply(update, context, "Action is not available anymore.", crm_menu_keyboard())

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        message = update.message
        if message is None:
            return False

        if message.forward_origin is not None and context.user_data.get(STATE_KEY, {}).get("action") != "await_forwarded":
            await self._handle_forwarded_message(update, context)
            return True

        state = context.user_data.get(STATE_KEY, {})
        action = state.get("action")
        if not action:
            return False

        if action == "await_forwarded":
            if message.forward_origin is None:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Forward a client message or tap CRM to cancel.",
                    reply_markup=crm_menu_keyboard(),
                )
                return True

            await self._handle_forwarded_message(update, context)
            return True

        if not message.text:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Send text for this step or tap CRM to cancel.",
                reply_markup=crm_menu_keyboard(),
            )
            return True

        if action == "create_name":
            name = message.text.strip()
            if not name:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Name is required. Send the lead name.",
                    reply_markup=crm_menu_keyboard(),
                )
                return True

            context.user_data.setdefault(CREATE_DRAFT_KEY, {})["name"] = name
            self._set_state(context, "create_phone")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Send the phone number or skip this field.",
                reply_markup=skip_phone_keyboard(),
            )
            return True

        if action == "create_phone":
            context.user_data.setdefault(CREATE_DRAFT_KEY, {})["phone"] = message.text.strip()
            await self._prompt_manual_reminder(update, context)
            return True

        if action == "edit_name":
            await self._apply_text_edit(update, context, "name", message.text.strip())
            return True

        if action == "edit_phone":
            await self._apply_text_edit(update, context, "phone", message.text.strip())
            return True

        return False

    async def _handle_forwarded_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        owner_user_id = update.effective_user.id
        owner_chat_id = update.effective_chat.id
        self._reset_state(context)
        forwarded_draft = self._build_forwarded_draft(update.message)
        duplicate = self.lead_service.find_duplicate(
            owner_user_id,
            telegram_user_id=forwarded_draft.telegram_user_id,
            telegram_username=forwarded_draft.telegram_username,
            name=forwarded_draft.name,
            source="telegram",
        )

        if duplicate:
            context.user_data[FORWARDED_DRAFT_KEY] = asdict(forwarded_draft)
            await context.bot.send_message(
                chat_id=owner_chat_id,
                text=f"Possible duplicate found: {duplicate.name}",
                reply_markup=duplicate_keyboard(duplicate.id),
            )
            return

        lead = self.lead_service.create_forwarded_lead(
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            draft=forwarded_draft,
        )
        self._reset_state(context)
        await context.bot.send_message(
            chat_id=owner_chat_id,
            text="Lead created from forwarded message.",
        )
        await self._send_lead_card(update, context, lead)

    async def _create_forwarded_duplicate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        draft_data = context.user_data.get(FORWARDED_DRAFT_KEY)
        if not draft_data:
            await self.open_crm(update, context)
            return

        lead = self.lead_service.create_forwarded_lead(
            owner_user_id=update.effective_user.id,
            owner_chat_id=update.effective_chat.id,
            draft=ForwardedLeadDraft(**draft_data),
        )
        self._reset_state(context)
        await self._send_lead_card(update, context, lead)

    async def _prompt_manual_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self._set_state(context, "create_reminder")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Choose the first reminder.",
            reply_markup=reminder_keyboard("create:rem"),
        )

    async def _complete_manual_creation(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        preset: str,
    ) -> None:
        draft = context.user_data.get(CREATE_DRAFT_KEY, {})
        if not draft.get("name") or not draft.get("lead_type") or not draft.get("source"):
            self._reset_state(context)
            await self._reply(update, context, "Lead draft expired. Start again from CRM.", crm_menu_keyboard())
            return

        lead = self.lead_service.create_manual_lead(
            owner_user_id=update.effective_user.id,
            owner_chat_id=update.effective_chat.id,
            name=draft["name"],
            phone=draft.get("phone"),
            lead_type=draft["lead_type"],
            source=draft["source"],
        )
        self._reset_state(context)

        if preset != "none":
            scheduled_at = self.reminder_service.schedule_from_preset(preset)
            lead, reminder = self.lead_service.set_reminder(update.effective_user.id, lead.id, scheduled_at)
            self.reminder_service.schedule_job(context.application, lead, reminder)

        await self._send_lead_card(update, context, lead)

    async def _show_lead_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        archived: bool,
    ) -> None:
        leads = self.lead_service.list_leads(update.effective_user.id, archived=archived)
        if not leads:
            title = "No archived leads." if archived else "No active leads yet."
            await self._reply(update, context, title, crm_menu_keyboard())
            return

        lines = []
        for index, lead in enumerate(leads, start=1):
            next_call = self.reminder_service.format_datetime(lead.next_call_at)
            lines.append(f"{index}. {lead.name} - {lead.status_label} - {next_call}")

        title = "Archived leads" if archived else "All leads"
        await self._reply(
            update,
            context,
            f"{title}\n\n" + "\n".join(lines),
            lead_list_keyboard(leads, archived=archived),
        )

    async def _show_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        overdue, today = self.lead_service.list_today(update.effective_user.id, self.reminder_service.now())
        if not overdue and not today:
            await self._reply(update, context, "No reminders for today.", crm_menu_keyboard())
            return

        sections = []
        if overdue:
            sections.append("Overdue")
            sections.extend(self._format_today_line(lead) for lead in overdue)

        if today:
            if sections:
                sections.append("")
            sections.append("Today")
            sections.extend(self._format_today_line(lead) for lead in today)

        await self._reply(
            update,
            context,
            "\n".join(sections),
            lead_list_keyboard(overdue + today),
        )

    async def _show_lead_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.get_lead(update.effective_user.id, lead_id)
        await self._send_lead_card(update, context, lead)

    async def _send_lead_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead: Lead) -> None:
        await self._reply(
            update,
            context,
            self._format_lead_card(lead),
            lead_card_keyboard(
                lead.id,
                archived=lead.is_archived,
                include_add_phone=lead.phone is None,
            ),
        )

    async def _show_edit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.get_lead(update.effective_user.id, lead_id)
        await self._reply(
            update,
            context,
            f"Edit {lead.name}",
            edit_menu_keyboard(lead.id),
        )

    async def _show_status_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        self.lead_service.get_lead(update.effective_user.id, lead_id)
        await self._reply(update, context, "Choose the new status.", status_keyboard(lead_id))

    async def _show_reminder_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        self.lead_service.get_lead(update.effective_user.id, lead_id)
        await self._reply(
            update,
            context,
            "Choose the reminder time.",
            reminder_keyboard("lead:remset", lead_id),
        )

    async def _set_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lead_id: int,
        status: str,
    ) -> None:
        lead = self.lead_service.update_status(update.effective_user.id, lead_id, status)
        await self._send_lead_card(update, context, lead)

    async def _set_type(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lead_id: int,
        lead_type: str,
    ) -> None:
        lead = self.lead_service.update_lead_type(update.effective_user.id, lead_id, lead_type)
        await self._send_lead_card(update, context, lead)

    async def _set_source(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lead_id: int,
        source: str,
    ) -> None:
        lead = self.lead_service.update_source(update.effective_user.id, lead_id, source)
        await self._send_lead_card(update, context, lead)

    async def _set_reminder(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lead_id: int,
        preset: str,
    ) -> None:
        if preset == "none":
            lead = self.lead_service.clear_reminder(update.effective_user.id, lead_id)
            self.reminder_service.cancel_job(context.application, lead_id)
            await self._send_lead_card(update, context, lead)
            return

        scheduled_at = self.reminder_service.schedule_from_preset(preset)
        lead, reminder = self.lead_service.set_reminder(update.effective_user.id, lead_id, scheduled_at)
        self.reminder_service.schedule_job(context.application, lead, reminder)
        await self._send_lead_card(update, context, lead)

    async def _mark_called(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.mark_called(
            update.effective_user.id,
            lead_id,
            self.reminder_service.now(),
        )
        self.reminder_service.cancel_job(context.application, lead_id)
        await self._send_lead_card(update, context, lead)

    async def _archive_lead(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.archive(update.effective_user.id, lead_id)
        self.reminder_service.cancel_job(context.application, lead_id)
        await self._send_lead_card(update, context, lead)

    async def _restore_lead(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.restore(update.effective_user.id, lead_id)
        await self._send_lead_card(update, context, lead)

    async def _clear_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
        lead = self.lead_service.update_phone(update.effective_user.id, lead_id, "")
        self._reset_state(context)
        await self._send_lead_card(update, context, lead)

    async def _apply_text_edit(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        field_name: str,
        value: str,
    ) -> None:
        lead_id = context.user_data[STATE_KEY]["lead_id"]
        try:
            if field_name == "name":
                lead = self.lead_service.update_name(update.effective_user.id, lead_id, value)
            else:
                lead = self.lead_service.update_phone(update.effective_user.id, lead_id, value)
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="This field cannot be empty. Send a value or tap CRM to cancel.",
                reply_markup=crm_menu_keyboard(),
            )
            return

        self._reset_state(context)
        await self._send_lead_card(update, context, lead)

    async def _reply(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        reply_markup,
    ) -> None:
        query = update.callback_query
        if query:
            try:
                await query.edit_message_text(text=text, reply_markup=reply_markup)
            except BadRequest as error:
                if "Message is not modified" not in str(error):
                    raise
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
            )

    def _set_state(self, context: ContextTypes.DEFAULT_TYPE, action: str, **payload) -> None:
        context.user_data[STATE_KEY] = {"action": action, **payload}

    def _reset_state(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.pop(STATE_KEY, None)
        context.user_data.pop(CREATE_DRAFT_KEY, None)
        context.user_data.pop(FORWARDED_DRAFT_KEY, None)

    def _build_forwarded_draft(self, message) -> ForwardedLeadDraft:
        origin = message.forward_origin
        fallback_name = f"Telegram Lead {int(datetime.utcnow().timestamp())}"

        if hasattr(origin, "sender_user") and origin.sender_user:
            user = origin.sender_user
            display_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
            display_name = display_name or user.username or fallback_name
            return ForwardedLeadDraft(
                name=display_name,
                telegram_user_id=str(user.id),
                telegram_username=user.username,
                telegram_display_name=display_name,
            )

        if hasattr(origin, "sender_user_name") and origin.sender_user_name:
            return ForwardedLeadDraft(
                name=origin.sender_user_name,
                telegram_user_id=None,
                telegram_username=None,
                telegram_display_name=origin.sender_user_name,
            )

        chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
        if chat:
            display_name = getattr(chat, "title", None) or fallback_name
            return ForwardedLeadDraft(
                name=display_name,
                telegram_user_id=None,
                telegram_username=getattr(chat, "username", None),
                telegram_display_name=display_name,
            )

        return ForwardedLeadDraft(
            name=fallback_name,
            telegram_user_id=None,
            telegram_username=None,
            telegram_display_name=fallback_name,
        )

    def _format_lead_card(self, lead: Lead) -> str:
        return (
            f"{lead.name}\n"
            f"Phone: {lead.phone or '-'}\n"
            f"Type: {lead.lead_type_label}\n"
            f"Source: {lead.source_label}\n"
            f"Status: {lead.status_label}\n"
            f"Next call: {self.reminder_service.format_datetime(lead.next_call_at)}\n"
            f"Last contact: {self.reminder_service.format_datetime(lead.last_contact_at)}"
        )

    def _format_today_line(self, lead: Lead) -> str:
        next_call = self.reminder_service.format_datetime(lead.next_call_at)
        return f"- {lead.name} - {lead.status_label} - {next_call}"
