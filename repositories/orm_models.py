from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from models.lead import Lead
from models.reminder import Reminder


class Base(DeclarativeBase):
    pass


class TZDateTime(TypeDecorator[datetime | None]):
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(DateTime(timezone=True))
        return dialect.type_descriptor(String())

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return value.isoformat()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)


class LeadRecord(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_leads_owner_archived", "owner_user_id", "is_archived", "updated_at"),
        Index("idx_leads_next_call", "owner_user_id", "next_call_at"),
        Index("idx_leads_telegram_user", "owner_user_id", "telegram_user_id"),
        Index("idx_leads_telegram_username", "owner_user_id", "telegram_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int]
    owner_chat_id: Mapped[int]
    name: Mapped[str]
    phone: Mapped[str | None]
    telegram_user_id: Mapped[str | None]
    telegram_username: Mapped[str | None]
    telegram_display_name: Mapped[str | None]
    lead_type: Mapped[str]
    source: Mapped[str]
    status: Mapped[str]
    next_call_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    last_contact_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    capture_method: Mapped[str]
    is_archived: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime())

    reminders: Mapped[list["ReminderRecord"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    def to_model(self) -> Lead:
        return Lead(
            id=self.id,
            owner_user_id=self.owner_user_id,
            owner_chat_id=self.owner_chat_id,
            name=self.name,
            phone=self.phone,
            telegram_user_id=self.telegram_user_id,
            telegram_username=self.telegram_username,
            telegram_display_name=self.telegram_display_name,
            lead_type=self.lead_type,
            source=self.source,
            status=self.status,
            next_call_at=self.next_call_at,
            last_contact_at=self.last_contact_at,
            capture_method=self.capture_method,
            is_archived=self.is_archived,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ReminderRecord(Base):
    __tablename__ = "lead_reminders"
    __table_args__ = (
        Index(
            "idx_active_reminder_per_lead",
            "lead_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(TZDateTime())
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(TZDateTime())
    created_at: Mapped[datetime] = mapped_column(TZDateTime())
    updated_at: Mapped[datetime] = mapped_column(TZDateTime())

    lead: Mapped[LeadRecord] = relationship(back_populates="reminders")

    def to_model(self) -> Reminder:
        return Reminder(
            id=self.id,
            lead_id=self.lead_id,
            scheduled_at=self.scheduled_at,
            is_active=self.is_active,
            sent_at=self.sent_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
