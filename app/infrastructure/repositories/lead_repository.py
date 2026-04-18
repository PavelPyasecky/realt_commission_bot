from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, select

from app.infrastructure.database.models import Lead


class LeadRepository:
    async def create(
        self,
        session,
        *,
        owner_user_id: int,
        owner_chat_id: int,
        name: str,
        phone: str | None,
        telegram_user_id: str | None,
        telegram_username: str | None,
        telegram_display_name: str | None,
        lead_type: str,
        source: str,
        status: str,
        next_call_at: datetime | None,
        last_contact_at: datetime | None,
        capture_method: str,
    ) -> Lead:
        record = Lead(
            owner_user_id=owner_user_id,
            owner_chat_id=owner_chat_id,
            name=name,
            phone=phone,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_display_name=telegram_display_name,
            lead_type=lead_type,
            source=source,
            status=status,
            next_call_at=next_call_at,
            last_contact_at=last_contact_at,
            capture_method=capture_method,
            is_archived=False,
        )
        session.add(record)
        await session.flush()
        await session.refresh(record)
        return record

    async def get_by_id(self, session, lead_id: int, owner_user_id: int | None = None) -> Lead | None:
        stmt = select(Lead).where(Lead.id == lead_id)
        if owner_user_id is not None:
            stmt = stmt.where(Lead.owner_user_id == owner_user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_fields(self, session, lead_id: int, owner_user_id: int, **fields) -> Lead | None:
        record = await self.get_by_id(session, lead_id, owner_user_id=owner_user_id)
        if record is None:
            return None
        for key, value in fields.items():
            setattr(record, key, value)
        await session.flush()
        await session.refresh(record)
        return record

    async def list_by_owner(self, session, owner_user_id: int, archived: bool = False) -> list[Lead]:
        stmt = (
            select(Lead)
            .where(
                Lead.owner_user_id == owner_user_id,
                Lead.is_archived == archived,
            )
            .order_by(
                case((Lead.next_call_at.is_(None), 1), else_=0),
                Lead.next_call_at.asc(),
                Lead.updated_at.desc(),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_telegram_user_id(self, session, owner_user_id: int, telegram_user_id: str) -> Lead | None:
        stmt = (
            select(Lead)
            .where(
                Lead.owner_user_id == owner_user_id,
                Lead.telegram_user_id == telegram_user_id,
                Lead.is_archived.is_(False),
            )
            .order_by(Lead.updated_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_telegram_username(self, session, owner_user_id: int, telegram_username: str) -> Lead | None:
        stmt = (
            select(Lead)
            .where(
                Lead.owner_user_id == owner_user_id,
                Lead.telegram_username == telegram_username,
                Lead.is_archived.is_(False),
            )
            .order_by(Lead.updated_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_source(self, session, owner_user_id: int, source: str) -> list[Lead]:
        stmt = (
            select(Lead)
            .where(
                Lead.owner_user_id == owner_user_id,
                Lead.source == source,
                Lead.is_archived.is_(False),
            )
            .order_by(Lead.updated_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
