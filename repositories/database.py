from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: str):
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_user_id INTEGER NOT NULL,
                    owner_chat_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NULL,
                    telegram_user_id TEXT NULL,
                    telegram_username TEXT NULL,
                    telegram_display_name TEXT NULL,
                    lead_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    next_call_at TEXT NULL,
                    last_contact_at TEXT NULL,
                    capture_method TEXT NOT NULL,
                    is_archived INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lead_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER NOT NULL,
                    scheduled_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    sent_at TEXT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_leads_owner_archived
                    ON leads(owner_user_id, is_archived, updated_at DESC);

                CREATE INDEX IF NOT EXISTS idx_leads_next_call
                    ON leads(owner_user_id, next_call_at);

                CREATE INDEX IF NOT EXISTS idx_leads_telegram_user
                    ON leads(owner_user_id, telegram_user_id);

                CREATE INDEX IF NOT EXISTS idx_leads_telegram_username
                    ON leads(owner_user_id, telegram_username);

                CREATE UNIQUE INDEX IF NOT EXISTS idx_active_reminder_per_lead
                    ON lead_reminders(lead_id)
                    WHERE is_active = 1;
                """
            )

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
