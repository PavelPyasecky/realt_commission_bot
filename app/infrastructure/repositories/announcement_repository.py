from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update

from app.infrastructure.database.models import Announcement


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnnouncementRepository:
    async def create(
        self,
        session,
        *,
        body_html: str,
        scheduled_at: datetime,
        created_by_user_id: int,
    ) -> Announcement:
        now = _utc_now()
        row = Announcement(
            body_html=body_html,
            scheduled_at=scheduled_at,
            created_by_user_id=created_by_user_id,
            sent_at=None,
            created_at=now,
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return row

    async def list_due(self, session, *, now: datetime, limit: int) -> list[Announcement]:
        stmt = (
            select(Announcement)
            .where(
                Announcement.sent_at.is_(None),
                Announcement.scheduled_at <= now,
            )
            .order_by(Announcement.scheduled_at.asc(), Announcement.id.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def mark_sent(self, session, announcement_id: int) -> None:
        now = _utc_now()
        await session.execute(
            update(Announcement)
            .where(Announcement.id == announcement_id)
            .values(sent_at=now)
        )
        await session.flush()
