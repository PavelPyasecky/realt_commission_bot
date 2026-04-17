from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import exceptions
from models.lead import Lead, normalize_text
from models.reminder import Reminder
from repositories.lead_repository import LeadRepository
from repositories.reminder_repository import ReminderRepository


@dataclass(slots=True)
class ForwardedLeadDraft:
    name: str
    telegram_user_id: str | None
    telegram_username: str | None
    telegram_display_name: str | None


class LeadService:
    def __init__(self, lead_repository: LeadRepository, reminder_repository: ReminderRepository):
        self.lead_repository = lead_repository
        self.reminder_repository = reminder_repository

    def create_manual_lead(
        self,
        *,
        owner_user_id: int,
        owner_chat_id: int,
        name: str,
        phone: str | None,
        lead_type: str,
        source: str,
    ) -> Lead:
        return self.lead_repository.create(
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            name=name.strip(),
            phone=self._normalize_optional_text(phone),
            telegram_user_id=None,
            telegram_username=None,
            telegram_display_name=None,
            lead_type=lead_type,
            source=source,
            status="new",
            next_call_at=None,
            last_contact_at=None,
            capture_method="manual",
        )

    def create_forwarded_lead(
        self,
        *,
        owner_user_id: int,
        owner_chat_id: int,
        draft: ForwardedLeadDraft,
    ) -> Lead:
        return self.lead_repository.create(
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            name=draft.name,
            phone=None,
            telegram_user_id=draft.telegram_user_id,
            telegram_username=draft.telegram_username,
            telegram_display_name=draft.telegram_display_name,
            lead_type="unknown",
            source="telegram",
            status="new",
            next_call_at=None,
            last_contact_at=None,
            capture_method="forwarded_message",
        )

    def find_duplicate(
        self,
        owner_user_id: int,
        *,
        telegram_user_id: str | None,
        telegram_username: str | None,
        name: str,
        source: str,
    ) -> Lead | None:
        if telegram_user_id:
            duplicate = self.lead_repository.find_by_telegram_user_id(owner_user_id, telegram_user_id)
            if duplicate:
                return duplicate

        if telegram_username:
            duplicate = self.lead_repository.find_by_telegram_username(owner_user_id, telegram_username)
            if duplicate:
                return duplicate

        normalized_name = normalize_text(name)
        for lead in self.lead_repository.list_by_source(owner_user_id, source):
            if normalize_text(lead.name) == normalized_name:
                return lead

        return None

    def get_lead(self, owner_user_id: int, lead_id: int) -> Lead:
        lead = self.lead_repository.get_by_id(lead_id, owner_user_id=owner_user_id)
        if lead is None:
            raise exceptions.LeadNotFoundError
        return lead

    def list_leads(self, owner_user_id: int, *, archived: bool = False) -> list[Lead]:
        return self.lead_repository.list_by_owner(owner_user_id, archived=archived)

    def list_today(self, owner_user_id: int, now: datetime) -> tuple[list[Lead], list[Lead]]:
        overdue: list[Lead] = []
        today: list[Lead] = []

        for lead in self.list_leads(owner_user_id):
            if lead.next_call_at is None:
                continue

            if lead.next_call_at <= now:
                overdue.append(lead)
                continue

            if lead.next_call_at.date() == now.date():
                today.append(lead)

        return overdue, today

    def update_name(self, owner_user_id: int, lead_id: int, name: str) -> Lead:
        return self._update_required_text(owner_user_id, lead_id, "name", name)

    def update_phone(self, owner_user_id: int, lead_id: int, phone: str) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(
                lead_id,
                owner_user_id,
                phone=self._normalize_optional_text(phone),
            )
        )

    def update_lead_type(self, owner_user_id: int, lead_id: int, lead_type: str) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(lead_id, owner_user_id, lead_type=lead_type)
        )

    def update_source(self, owner_user_id: int, lead_id: int, source: str) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(self.lead_repository.update_fields(lead_id, owner_user_id, source=source))

    def update_status(self, owner_user_id: int, lead_id: int, status: str) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(self.lead_repository.update_fields(lead_id, owner_user_id, status=status))

    def archive(self, owner_user_id: int, lead_id: int) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        self.reminder_repository.clear_active(lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(
                lead_id,
                owner_user_id,
                is_archived=1,
                next_call_at=None,
            )
        )

    def restore(self, owner_user_id: int, lead_id: int) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(self.lead_repository.update_fields(lead_id, owner_user_id, is_archived=0))

    def mark_called(self, owner_user_id: int, lead_id: int, now: datetime) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        self.reminder_repository.clear_active(lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(
                lead_id,
                owner_user_id,
                last_contact_at=now,
                next_call_at=None,
            )
        )

    def set_reminder(self, owner_user_id: int, lead_id: int, scheduled_at: datetime) -> tuple[Lead, Reminder]:
        self.get_lead(owner_user_id, lead_id)
        reminder = self.reminder_repository.set_active(lead_id, scheduled_at)
        lead = self._require_lead(
            self.lead_repository.update_fields(
                lead_id,
                owner_user_id,
                next_call_at=scheduled_at,
            )
        )
        return lead, reminder

    def clear_reminder(self, owner_user_id: int, lead_id: int) -> Lead:
        self.get_lead(owner_user_id, lead_id)
        self.reminder_repository.clear_active(lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(
                lead_id,
                owner_user_id,
                next_call_at=None,
            )
        )

    def get_active_reminder(self, lead_id: int) -> Reminder | None:
        return self.reminder_repository.get_active(lead_id)

    def mark_reminder_sent(self, reminder_id: int) -> Reminder | None:
        return self.reminder_repository.mark_sent(reminder_id)

    def list_active_reminders(self) -> list[tuple[Lead, Reminder]]:
        active_pairs: list[tuple[Lead, Reminder]] = []

        for reminder in self.reminder_repository.list_active():
            lead = self.lead_repository.get_by_id(reminder.lead_id)
            if lead and not lead.is_archived:
                active_pairs.append((lead, reminder))

        return active_pairs

    def _update_required_text(self, owner_user_id: int, lead_id: int, field_name: str, value: str) -> Lead:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{field_name} is required")

        self.get_lead(owner_user_id, lead_id)
        return self._require_lead(
            self.lead_repository.update_fields(lead_id, owner_user_id, **{field_name: normalized_value})
        )

    @staticmethod
    def _require_lead(lead: Lead | None) -> Lead:
        if lead is None:
            raise exceptions.LeadNotFoundError
        return lead

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()
        return normalized_value or None
