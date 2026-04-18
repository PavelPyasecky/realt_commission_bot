from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.infrastructure.database.models import LeadReminder


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LeadReminderRepository:
    async def set_active(self, session, lead_id: int, scheduled_at: datetime) -> LeadReminder:
        now = _utc_now()
        result = await session.execute(
            select(LeadReminder).where(
                LeadReminder.lead_id == lead_id,
                LeadReminder.is_active.is_(True),
            )
        )
        active_records = result.scalars().all()
        for record in active_records:
            record.is_active = False
            record.updated_at = now

        record = LeadReminder(
            lead_id=lead_id,
            scheduled_at=scheduled_at,
            is_active=True,
            sent_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    async def clear_active(self, session, lead_id: int) -> None:
        now = _utc_now()
        result = await session.execute(
            select(LeadReminder).where(
                LeadReminder.lead_id == lead_id,
                LeadReminder.is_active.is_(True),
            )
        )
        for record in result.scalars().all():
            record.is_active = False
            record.updated_at = now
        await session.flush()

    async def get_active(self, session, lead_id: int) -> LeadReminder | None:
        result = await session.execute(
            select(LeadReminder).where(
                LeadReminder.lead_id == lead_id,
                LeadReminder.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()
