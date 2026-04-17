from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.crm_options import LEAD_TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS


def label_for(mapping: dict[str, str], value: str | None) -> str:
    if not value:
        return "-"
    return mapping.get(value, value)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().split())


@dataclass(slots=True)
class Lead:
    id: int
    owner_user_id: int
    owner_chat_id: int
    name: str
    phone: str | None
    telegram_user_id: str | None
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
        return label_for(LEAD_TYPE_LABELS, self.lead_type)

    @property
    def source_label(self) -> str:
        return label_for(SOURCE_LABELS, self.source)

    @property
    def status_label(self) -> str:
        return label_for(STATUS_LABELS, self.status)
