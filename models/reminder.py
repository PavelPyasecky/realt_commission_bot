from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Reminder:
    id: int
    lead_id: int
    scheduled_at: datetime
    is_active: bool
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
