from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from repositories.orm_models import Base


class Database:
    def __init__(self, url: str):
        self.url = url
        self.sa_url: URL = make_url(url)
        self.engine: Engine = create_engine(
            self.sa_url,
            future=True,
            pool_pre_ping=True,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            future=True,
        )
        self._configure_sqlite()

    def initialize(self) -> None:
        if self.sa_url.get_backend_name() == "sqlite" and self.sa_url.database:
            Path(self.sa_url.database).parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _configure_sqlite(self) -> None:
        if self.sa_url.get_backend_name() != "sqlite":
            return

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
