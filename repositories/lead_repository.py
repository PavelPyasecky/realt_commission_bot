from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import case, select

from models.lead import Lead
from repositories.database import Database
from repositories.orm_models import LeadRecord


def _utc_now() -> datetime:
    return datetime.now(UTC)


class LeadRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
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
        now = _utc_now()
        record = LeadRecord(
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
            created_at=now,
            updated_at=now,
        )

        with self.database.session() as session:
            session.add(record)
            session.flush()
            session.refresh(record)
            return record.to_model()

    def get_by_id(self, lead_id: int, *, owner_user_id: int | None = None) -> Lead | None:
        with self.database.session() as session:
            statement = select(LeadRecord).where(LeadRecord.id == lead_id)
            if owner_user_id is not None:
                statement = statement.where(LeadRecord.owner_user_id == owner_user_id)
            record = session.scalar(statement)
            return record.to_model() if record else None

    def update_fields(self, lead_id: int, owner_user_id: int, **fields: Any) -> Lead | None:
        with self.database.session() as session:
            record = session.scalar(
                select(LeadRecord).where(
                    LeadRecord.id == lead_id,
                    LeadRecord.owner_user_id == owner_user_id,
                )
            )
            if record is None:
                return None

            for key, value in fields.items():
                setattr(record, key, value)
            record.updated_at = _utc_now()
            session.flush()
            session.refresh(record)
            return record.to_model()

    def list_by_owner(self, owner_user_id: int, *, archived: bool = False) -> list[Lead]:
        with self.database.session() as session:
            statement = (
                select(LeadRecord)
                .where(
                    LeadRecord.owner_user_id == owner_user_id,
                    LeadRecord.is_archived == archived,
                )
                .order_by(
                    case((LeadRecord.next_call_at.is_(None), 1), else_=0),
                    LeadRecord.next_call_at.asc(),
                    LeadRecord.updated_at.desc(),
                )
            )
            records = session.scalars(statement).all()
            return [record.to_model() for record in records]

    def find_by_telegram_user_id(self, owner_user_id: int, telegram_user_id: str) -> Lead | None:
        with self.database.session() as session:
            statement = (
                select(LeadRecord)
                .where(
                    LeadRecord.owner_user_id == owner_user_id,
                    LeadRecord.telegram_user_id == telegram_user_id,
                    LeadRecord.is_archived.is_(False),
                )
                .order_by(LeadRecord.updated_at.desc())
                .limit(1)
            )
            record = session.scalar(statement)
            return record.to_model() if record else None

    def find_by_telegram_username(self, owner_user_id: int, telegram_username: str) -> Lead | None:
        with self.database.session() as session:
            statement = (
                select(LeadRecord)
                .where(
                    LeadRecord.owner_user_id == owner_user_id,
                    LeadRecord.telegram_username == telegram_username,
                    LeadRecord.is_archived.is_(False),
                )
                .order_by(LeadRecord.updated_at.desc())
                .limit(1)
            )
            record = session.scalar(statement)
            return record.to_model() if record else None

    def list_by_source(self, owner_user_id: int, source: str) -> list[Lead]:
        with self.database.session() as session:
            statement = (
                select(LeadRecord)
                .where(
                    LeadRecord.owner_user_id == owner_user_id,
                    LeadRecord.source == source,
                    LeadRecord.is_archived.is_(False),
                )
                .order_by(LeadRecord.updated_at.desc())
            )
            records = session.scalars(statement).all()
            return [record.to_model() for record in records]
