from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    is_subscribed = Column(Boolean, default=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(BigInteger, nullable=False, index=True)
    owner_chat_id = Column(BigInteger, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(255), nullable=True)
    telegram_user_id = Column(String(255), nullable=True, index=True)
    telegram_username = Column(String(255), nullable=True, index=True)
    telegram_display_name = Column(String(255), nullable=True)
    lead_type = Column(String(64), nullable=False, default="unknown")
    source = Column(String(64), nullable=False, default="telegram")
    status = Column(String(64), nullable=False, default="new")
    next_call_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    capture_method = Column(String(64), nullable=False, default="manual")
    is_archived = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    reminders = relationship(
        "LeadReminder",
        back_populates="lead",
        cascade="all, delete-orphan",
    )


class LeadReminder(Base):
    __tablename__ = "lead_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="reminders")


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    body_html = Column(Text, nullable=False)
    body_plain = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by_user_id = Column(BigInteger, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    state = Column(String(16), nullable=False, default="pending", server_default=text("'pending'"), index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
