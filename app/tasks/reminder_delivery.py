import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.bot.keyboards.crm import build_lead_card_keyboard
from app.infrastructure.database.transaction import managed_session
from app.infrastructure.repositories.lead_repository import LeadRepository
from app.infrastructure.repositories.lead_reminder_repository import LeadReminderRepository
from app.i18n import get_translator
from app.services.crm_options import LEAD_TYPE_LABELS, SOURCE_LABELS, STATUS_LABELS

logger = logging.getLogger(__name__)

_process_lock = asyncio.Lock()


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


@dataclass(frozen=True, slots=True)
class _ReminderDelivery:
    reminder_id: int
    lead_id: int
    chat_id: int
    name: str
    phone: str | None
    lead_type: str
    source: str
    status: str
    next_call_at: datetime | None
    is_archived: bool


def _reminder_message(_, row: _ReminderDelivery) -> str:
    type_raw = LEAD_TYPE_LABELS.get(row.lead_type, row.lead_type)
    source_raw = SOURCE_LABELS.get(row.source, row.source)
    status_raw = STATUS_LABELS.get(row.status, row.status)
    type_label = _(type_raw) if type_raw in LEAD_TYPE_LABELS.values() else type_raw
    source_label = _(source_raw) if source_raw in SOURCE_LABELS.values() else source_raw
    status_label = _(status_raw) if status_raw in STATUS_LABELS.values() else status_raw
    return (
        f"<b>{_('Lead reminder title')}</b>\n"
        f"{row.name}\n"
        f"{_('Lead card phone')}: {row.phone or '-'}\n"
        f"{_('Lead card type')}: {type_label}\n"
        f"{_('Lead card source')}: {source_label}\n"
        f"{_('Lead card status')}: {status_label}\n"
        f"{_('Lead card next call')}: {_format_dt(row.next_call_at)}"
    )


async def deliver_due_reminders(bot, sessionmaker, *, batch_limit: int) -> None:
    if batch_limit <= 0:
        return
    async with _process_lock:
        now = datetime.now(timezone.utc)
        reminder_repo = LeadReminderRepository()
        lead_repo = LeadRepository()
        _ = get_translator()

        async with managed_session(sessionmaker) as session:
            due = await reminder_repo.list_due_for_delivery(session, now=now, limit=batch_limit)
            rows: list[_ReminderDelivery] = []
            for reminder in due:
                lead = await lead_repo.get_by_id(session, reminder.lead_id, owner_user_id=None)
                if lead is None:
                    continue
                rows.append(
                    _ReminderDelivery(
                        reminder_id=reminder.id,
                        lead_id=lead.id,
                        chat_id=lead.owner_chat_id,
                        name=lead.name,
                        phone=lead.phone,
                        lead_type=lead.lead_type,
                        source=lead.source,
                        status=lead.status,
                        next_call_at=lead.next_call_at,
                        is_archived=lead.is_archived,
                    )
                )

        reminder_repo = LeadReminderRepository()
        for row in rows:
            if row.is_archived:
                async with managed_session(sessionmaker) as session:
                    await reminder_repo.mark_delivered(session, row.reminder_id)
                continue

            text = _reminder_message(_, row)
            keyboard = build_lead_card_keyboard(
                row.lead_id,
                archived=row.is_archived,
                include_add_phone=row.phone is None,
                _=_,
            )
            try:
                await bot.send_message(row.chat_id, text, reply_markup=keyboard)
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                logger.warning(
                    "Could not deliver lead reminder id=%s to chat_id=%s: %s",
                    row.reminder_id,
                    row.chat_id,
                    exc,
                )
            except Exception:
                logger.exception("Unexpected error delivering lead reminder id=%s", row.reminder_id)
                continue

            async with managed_session(sessionmaker) as session:
                await reminder_repo.mark_delivered(session, row.reminder_id)


async def reminder_delivery_loop(bot, sessionmaker, interval_seconds: float, batch_limit: int) -> None:
    while True:
        try:
            await deliver_due_reminders(bot, sessionmaker, batch_limit=batch_limit)
        except Exception:
            logger.exception("Reminder delivery tick failed")
        await asyncio.sleep(interval_seconds)
