from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update

from app.infrastructure.database.models import Announcement


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnnouncementRepository:
    async def create(
        self,
        session,
        *,
        body_html: str,
        body_plain: str | None,
        scheduled_at: datetime,
        created_by_user_id: int,
    ) -> Announcement:
        now = _utc_now()
        row = Announcement(
            body_html=body_html,
            body_plain=body_plain,
            scheduled_at=scheduled_at,
            created_by_user_id=created_by_user_id,
            sent_at=None,
            state="pending",
            error_message=None,
            created_at=now,
        )
        session.add(row)
        await session.flush()
        await session.refresh(row)
        return row

    async def get_by_id(self, session, announcement_id: int) -> Announcement | None:
        return await session.get(Announcement, announcement_id)

    async def list_by_state(
        self,
        session,
        *,
        state: str,
        limit: int,
        offset: int,
    ) -> list[Announcement]:
        stmt = (
            select(Announcement)
            .where(Announcement.state == state)
            .order_by(Announcement.scheduled_at.desc(), Announcement.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_state(self, session, *, state: str) -> int:
        stmt = select(func.count(Announcement.id)).where(Announcement.state == state)
        result = await session.execute(stmt)
        return int(result.scalar_one())

    async def list_due(self, session, *, now: datetime, limit: int) -> list[Announcement]:
        stmt = (
            select(Announcement)
            .where(
                Announcement.state == "pending",
                Announcement.scheduled_at <= now,
            )
            .order_by(Announcement.scheduled_at.asc(), Announcement.id.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def set_state(self, session, announcement_id: int, state: str) -> None:
        await session.execute(
            update(Announcement).where(Announcement.id == announcement_id).values(state=state)
        )
        await session.flush()

    async def mark_sending(self, session, announcement_id: int) -> None:
        await self.set_state(session, announcement_id, "sending")

    async def mark_sent(self, session, announcement_id: int) -> None:
        now = _utc_now()
        await session.execute(
            update(Announcement)
            .where(Announcement.id == announcement_id)
            .values(sent_at=now, state="sent", error_message=None)
        )
        await session.flush()

    async def mark_failed(self, session, announcement_id: int, error: str) -> None:
        text = (error or "")[:4000]
        await session.execute(
            update(Announcement)
            .where(Announcement.id == announcement_id)
            .values(state="failed", error_message=text)
        )
        await session.flush()

    async def cancel(self, session, announcement_id: int) -> bool:
        result = await session.execute(
            update(Announcement)
            .where(Announcement.id == announcement_id, Announcement.state == "pending")
            .values(state="cancelled")
        )
        await session.flush()
        return result.rowcount > 0

    async def delete(self, session, announcement_id: int) -> bool:
        result = await session.execute(delete(Announcement).where(Announcement.id == announcement_id))
        await session.flush()
        return result.rowcount > 0

    async def update_schedule(self, session, announcement_id: int, scheduled_at: datetime) -> bool:
        result = await session.execute(
            update(Announcement)
            .where(
                Announcement.id == announcement_id,
                Announcement.state.in_(("pending", "failed")),
            )
            .values(scheduled_at=scheduled_at, state="pending", error_message=None)
        )
        await session.flush()
        return result.rowcount > 0

    async def update_body(
        self,
        session,
        announcement_id: int,
        *,
        body_html: str,
        body_plain: str | None,
    ) -> bool:
        result = await session.execute(
            update(Announcement)
            .where(
                Announcement.id == announcement_id,
                Announcement.state.in_(("pending", "failed")),
            )
            .values(body_html=body_html, body_plain=body_plain, state="pending", error_message=None)
        )
        await session.flush()
        return result.rowcount > 0
