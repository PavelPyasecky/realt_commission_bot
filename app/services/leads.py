from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.infrastructure.repositories.lead_reminder_repository import LeadReminderRepository
from app.services.crm_options import LEAD_TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().split())


def format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


@dataclass(slots=True)
class LeadView:
    id: int
    owner_user_id: int
    owner_chat_id: int
    name: str
    phone: str | None
    telegram_user_id: int | None
    telegram_username: str | None
    telegram_display_name: str | None
    lead_type: str
    source: str
    status: str
    next_call_at: datetime | None
    last_contact_at: datetime | None
    capture_method: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    @property
    def lead_type_label(self) -> str:
        return LEAD_TYPE_LABELS.get(self.lead_type, self.lead_type)

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.source, self.source)

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)


@dataclass(slots=True)
class ForwardedLeadDraft:
    name: str
    telegram_user_id: int | None
    telegram_username: str | None
    telegram_display_name: str | None


class ReminderPlanner:
    PRESET_MAP = {
        "1h": lambda now: now + timedelta(hours=1),
        "t18": lambda now: _today_or_tomorrow(now, 18, 0),
        "tm10": lambda now: (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0),
        "3d": lambda now: (now + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0),
        "1w": lambda now: (now + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0),
    }

    @classmethod
    def schedule(cls, preset: str, now: datetime | None = None) -> datetime | None:
        if preset == "none":
            return None
        base = now or datetime.now(timezone.utc)
        factory = cls.PRESET_MAP.get(preset)
        if factory is None:
            raise ValueError(f"Unknown reminder preset: {preset}")
        return factory(base)


def _today_or_tomorrow(now: datetime, hour: int, minute: int) -> datetime:
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target


class LeadService:
    def __init__(self, lead_repository=None, reminder_repository=None):
        from app.infrastructure.repositories.lead_repository import LeadRepository

        self.lead_repository = lead_repository or LeadRepository()
        self.reminder_repository = reminder_repository or LeadReminderRepository()

    async def create_manual_lead(
        self,
        session,
        *,
        owner_user_id: int,
        owner_chat_id: int,
        name: str,
        phone: str | None,
        lead_type: str,
        source: str,
    ):
        return await self.lead_repository.create(
            session,
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

    async def create_forwarded_lead(
        self,
        session,
        *,
        owner_user_id: int,
        owner_chat_id: int,
        draft: ForwardedLeadDraft,
    ):
        return await self.lead_repository.create(
            session,
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            name=draft.name,
            phone=None,
            telegram_user_id=str(draft.telegram_user_id) if draft.telegram_user_id is not None else None,
            telegram_username=draft.telegram_username,
            telegram_display_name=draft.telegram_display_name,
            lead_type="unknown",
            source="telegram",
            status="new",
            next_call_at=None,
            last_contact_at=None,
            capture_method="forwarded_message",
        )

    async def find_duplicate(
        self,
        session,
        *,
        owner_user_id: int,
        telegram_user_id: str | None,
        telegram_username: str | None,
        name: str,
        source: str,
    ):
        if telegram_user_id:
            duplicate = await self.lead_repository.find_by_telegram_user_id(session, owner_user_id, telegram_user_id)
            if duplicate:
                return duplicate

        if telegram_username:
            duplicate = await self.lead_repository.find_by_telegram_username(session, owner_user_id, telegram_username)
            if duplicate:
                return duplicate

        normalized_name = normalize_text(name)
        for lead in await self.lead_repository.list_by_source(session, owner_user_id, source):
            if normalize_text(lead.name) == normalized_name:
                return lead
        return None

    async def get_lead(self, session, owner_user_id: int, lead_id: int):
        lead = await self.lead_repository.get_by_id(session, lead_id, owner_user_id=owner_user_id)
        if lead is None:
            raise ValueError("Lead not found")
        return lead

    async def list_leads(self, session, owner_user_id: int, archived: bool = False):
        return await self.lead_repository.list_by_owner(session, owner_user_id, archived=archived)

    async def list_today(self, session, owner_user_id: int):
        now = datetime.now(timezone.utc)
        overdue = []
        today = []
        for lead in await self.list_leads(session, owner_user_id, archived=False):
            if lead.next_call_at is None:
                continue
            if lead.next_call_at <= now:
                overdue.append(lead)
            elif lead.next_call_at.date() == now.date():
                today.append(lead)
        return overdue, today

    async def update_name(self, session, owner_user_id: int, lead_id: int, name: str):
        return await self._update_required_text(session, owner_user_id, lead_id, "name", name)

    async def update_phone(self, session, owner_user_id: int, lead_id: int, phone: str):
        await self.get_lead(session, owner_user_id, lead_id)
        lead = await self.lead_repository.update_fields(
            session,
            lead_id,
            owner_user_id,
            phone=self._normalize_optional_text(phone),
        )
        return self._require_lead(lead)

    async def update_lead_type(self, session, owner_user_id: int, lead_id: int, lead_type: str):
        await self.get_lead(session, owner_user_id, lead_id)
        return self._require_lead(await self.lead_repository.update_fields(session, lead_id, owner_user_id, lead_type=lead_type))

    async def update_source(self, session, owner_user_id: int, lead_id: int, source: str):
        await self.get_lead(session, owner_user_id, lead_id)
        return self._require_lead(await self.lead_repository.update_fields(session, lead_id, owner_user_id, source=source))

    async def update_status(self, session, owner_user_id: int, lead_id: int, status: str):
        await self.get_lead(session, owner_user_id, lead_id)
        return self._require_lead(await self.lead_repository.update_fields(session, lead_id, owner_user_id, status=status))

    async def archive(self, session, owner_user_id: int, lead_id: int):
        await self.get_lead(session, owner_user_id, lead_id)
        await self.reminder_repository.clear_active(session, lead_id)
        return self._require_lead(
            await self.lead_repository.update_fields(
                session,
                lead_id,
                owner_user_id,
                is_archived=True,
                next_call_at=None,
            )
        )

    async def restore(self, session, owner_user_id: int, lead_id: int):
        await self.get_lead(session, owner_user_id, lead_id)
        return self._require_lead(await self.lead_repository.update_fields(session, lead_id, owner_user_id, is_archived=False))

    async def mark_called(self, session, owner_user_id: int, lead_id: int):
        await self.get_lead(session, owner_user_id, lead_id)
        await self.reminder_repository.clear_active(session, lead_id)
        return self._require_lead(
            await self.lead_repository.update_fields(
                session,
                lead_id,
                owner_user_id,
                last_contact_at=datetime.now(timezone.utc),
                next_call_at=None,
            )
        )

    async def set_reminder(self, session, owner_user_id: int, lead_id: int, scheduled_at: datetime):
        await self.get_lead(session, owner_user_id, lead_id)
        await self.reminder_repository.set_active(session, lead_id, scheduled_at)
        return self._require_lead(
            await self.lead_repository.update_fields(
                session,
                lead_id,
                owner_user_id,
                next_call_at=scheduled_at,
            )
        )

    async def clear_reminder(self, session, owner_user_id: int, lead_id: int):
        await self.get_lead(session, owner_user_id, lead_id)
        await self.reminder_repository.clear_active(session, lead_id)
        return self._require_lead(
            await self.lead_repository.update_fields(
                session,
                lead_id,
                owner_user_id,
                next_call_at=None,
            )
        )

    @staticmethod
    def schedule_from_preset(preset: str):
        return ReminderPlanner.schedule(preset)

    async def _update_required_text(self, session, owner_user_id: int, lead_id: int, field_name: str, value: str):
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{field_name} is required")
        await self.get_lead(session, owner_user_id, lead_id)
        return self._require_lead(
            await self.lead_repository.update_fields(
                session,
                lead_id,
                owner_user_id,
                **{field_name: normalized_value},
            )
        )

    @staticmethod
    def _require_lead(lead):
        if lead is None:
            raise ValueError("Lead not found")
        return lead

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None
