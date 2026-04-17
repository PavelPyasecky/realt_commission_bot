from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from models.lead import Lead
from repositories.database import Database


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


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

        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    owner_user_id,
                    owner_chat_id,
                    name,
                    phone,
                    telegram_user_id,
                    telegram_username,
                    telegram_display_name,
                    lead_type,
                    source,
                    status,
                    next_call_at,
                    last_contact_at,
                    capture_method,
                    is_archived,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    owner_user_id,
                    owner_chat_id,
                    name,
                    phone,
                    telegram_user_id,
                    telegram_username,
                    telegram_display_name,
                    lead_type,
                    source,
                    status,
                    _serialize_datetime(next_call_at),
                    _serialize_datetime(last_contact_at),
                    capture_method,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

            lead_id = cursor.lastrowid

        return self.get_by_id(lead_id, owner_user_id=owner_user_id)

    def get_by_id(self, lead_id: int, *, owner_user_id: int | None = None) -> Lead | None:
        query = "SELECT * FROM leads WHERE id = ?"
        params: list[Any] = [lead_id]

        if owner_user_id is not None:
            query += " AND owner_user_id = ?"
            params.append(owner_user_id)

        with self.database.connection() as connection:
            row = connection.execute(query, params).fetchone()

        return self._row_to_lead(row) if row else None

    def update_fields(self, lead_id: int, owner_user_id: int, **fields: Any) -> Lead | None:
        if not fields:
            return self.get_by_id(lead_id, owner_user_id=owner_user_id)

        normalized_fields = {
            key: _serialize_datetime(value) if isinstance(value, datetime) else value
            for key, value in fields.items()
        }
        normalized_fields["updated_at"] = _utc_now().isoformat()

        assignments = ", ".join(f"{key} = ?" for key in normalized_fields)
        params = list(normalized_fields.values()) + [lead_id, owner_user_id]

        with self.database.connection() as connection:
            connection.execute(
                f"UPDATE leads SET {assignments} WHERE id = ? AND owner_user_id = ?",
                params,
            )

        return self.get_by_id(lead_id, owner_user_id=owner_user_id)

    def list_by_owner(self, owner_user_id: int, *, archived: bool = False) -> list[Lead]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ? AND is_archived = ?
                ORDER BY
                    CASE WHEN next_call_at IS NULL THEN 1 ELSE 0 END,
                    next_call_at ASC,
                    updated_at DESC
                """,
                (owner_user_id, int(archived)),
            ).fetchall()

        return [self._row_to_lead(row) for row in rows]

    def find_by_telegram_user_id(self, owner_user_id: int, telegram_user_id: str) -> Lead | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ? AND telegram_user_id = ? AND is_archived = 0
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (owner_user_id, telegram_user_id),
            ).fetchone()

        return self._row_to_lead(row) if row else None

    def find_by_telegram_username(self, owner_user_id: int, telegram_username: str) -> Lead | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ? AND telegram_username = ? AND is_archived = 0
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (owner_user_id, telegram_username),
            ).fetchone()

        return self._row_to_lead(row) if row else None

    def list_by_source(self, owner_user_id: int, source: str) -> list[Lead]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ? AND source = ? AND is_archived = 0
                ORDER BY updated_at DESC
                """,
                (owner_user_id, source),
            ).fetchall()

        return [self._row_to_lead(row) for row in rows]

    def _row_to_lead(self, row: Any) -> Lead:
        return Lead(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            owner_chat_id=row["owner_chat_id"],
            name=row["name"],
            phone=row["phone"],
            telegram_user_id=row["telegram_user_id"],
            telegram_username=row["telegram_username"],
            telegram_display_name=row["telegram_display_name"],
            lead_type=row["lead_type"],
            source=row["source"],
            status=row["status"],
            next_call_at=_parse_datetime(row["next_call_at"]),
            last_contact_at=_parse_datetime(row["last_contact_at"]),
            capture_method=row["capture_method"],
            is_archived=bool(row["is_archived"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
