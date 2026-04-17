from __future__ import annotations

from datetime import UTC, datetime

from models.reminder import Reminder
from repositories.database import Database


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class ReminderRepository:
    def __init__(self, database: Database):
        self.database = database

    def set_active(self, lead_id: int, scheduled_at: datetime) -> Reminder:
        now = datetime.now(UTC).isoformat()

        with self.database.connection() as connection:
            connection.execute(
                "UPDATE lead_reminders SET is_active = 0, updated_at = ? WHERE lead_id = ? AND is_active = 1",
                (now, lead_id),
            )
            cursor = connection.execute(
                """
                INSERT INTO lead_reminders (
                    lead_id,
                    scheduled_at,
                    is_active,
                    sent_at,
                    created_at,
                    updated_at
                ) VALUES (?, ?, 1, NULL, ?, ?)
                """,
                (lead_id, scheduled_at.isoformat(), now, now),
            )

            reminder_id = cursor.lastrowid

        return self.get_by_id(reminder_id)

    def clear_active(self, lead_id: int) -> None:
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE lead_reminders
                SET is_active = 0, updated_at = ?
                WHERE lead_id = ? AND is_active = 1
                """,
                (datetime.now(UTC).isoformat(), lead_id),
            )

    def get_active(self, lead_id: int) -> Reminder | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM lead_reminders
                WHERE lead_id = ? AND is_active = 1
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

        return self._row_to_reminder(row) if row else None

    def get_by_id(self, reminder_id: int) -> Reminder | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM lead_reminders WHERE id = ?",
                (reminder_id,),
            ).fetchone()

        return self._row_to_reminder(row) if row else None

    def list_active(self) -> list[Reminder]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM lead_reminders
                WHERE is_active = 1
                ORDER BY scheduled_at ASC
                """
            ).fetchall()

        return [self._row_to_reminder(row) for row in rows]

    def mark_sent(self, reminder_id: int) -> Reminder | None:
        now = datetime.now(UTC).isoformat()
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE lead_reminders
                SET sent_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, reminder_id),
            )

        return self.get_by_id(reminder_id)

    def _row_to_reminder(self, row) -> Reminder:
        return Reminder(
            id=row["id"],
            lead_id=row["lead_id"],
            scheduled_at=datetime.fromisoformat(row["scheduled_at"]),
            is_active=bool(row["is_active"]),
            sent_at=_parse_datetime(row["sent_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
