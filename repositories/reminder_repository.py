from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from models.reminder import Reminder
from repositories.database import Database
from repositories.orm_models import ReminderRecord


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ReminderRepository:
    def __init__(self, database: Database):
        self.database = database

    def set_active(self, lead_id: int, scheduled_at: datetime) -> Reminder:
        now = _utc_now()
        with self.database.session() as session:
            active_records = session.scalars(
                select(ReminderRecord).where(
                    ReminderRecord.lead_id == lead_id,
                    ReminderRecord.is_active.is_(True),
                )
            ).all()
            for record in active_records:
                record.is_active = False
                record.updated_at = now

            record = ReminderRecord(
                lead_id=lead_id,
                scheduled_at=scheduled_at,
                is_active=True,
                sent_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            session.refresh(record)
            return record.to_model()

    def clear_active(self, lead_id: int) -> None:
        now = _utc_now()
        with self.database.session() as session:
            records = session.scalars(
                select(ReminderRecord).where(
                    ReminderRecord.lead_id == lead_id,
                    ReminderRecord.is_active.is_(True),
                )
            ).all()
            for record in records:
                record.is_active = False
                record.updated_at = now
            session.flush()

    def get_active(self, lead_id: int) -> Reminder | None:
        with self.database.session() as session:
            record = session.scalar(
                select(ReminderRecord).where(
                    ReminderRecord.lead_id == lead_id,
                    ReminderRecord.is_active.is_(True),
                )
            )
            return record.to_model() if record else None

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        with self.database.session() as session:
            record = session.scalar(select(ReminderRecord).where(ReminderRecord.id == reminder_id))
            return record.to_model() if record else None

    def list_active(self) -> list[Reminder]:
        with self.database.session() as session:
            records = session.scalars(
                select(ReminderRecord)
                .where(ReminderRecord.is_active.is_(True))
                .order_by(ReminderRecord.scheduled_at.asc())
            ).all()
            return [record.to_model() for record in records]

    def mark_sent(self, reminder_id: int) -> Reminder | None:
        now = _utc_now()
        with self.database.session() as session:
            record = session.scalar(select(ReminderRecord).where(ReminderRecord.id == reminder_id))
            if record is None:
                return None

            record.sent_at = now
            record.updated_at = now
            session.flush()
            session.refresh(record)
            return record.to_model()
