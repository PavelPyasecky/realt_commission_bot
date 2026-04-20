from __future__ import annotations

import html
import re
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from zoneinfo import ZoneInfo

from app.core.config import config
from app.infrastructure.database.transaction import managed_session
from app.infrastructure.repositories.announcement_repository import AnnouncementRepository
from app.i18n import get_translator

router = Router()
_announce_repo = AnnouncementRepository()

_DATETIME_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*$")


class AnnounceFlow(StatesGroup):
    schedule = State()
    body = State()


def _is_admin(user_id: int | None, chat_id: int | None) -> bool:
    if user_id is not None and user_id in config.ADMIN_ID:
        return True
    if chat_id is not None and chat_id in config.ADMIN_ID:
        return True
    return False


def _parse_schedule(text: str) -> datetime:
    m = _DATETIME_RE.match(text or "")
    if not m:
        raise ValueError("bad_format")
    y, mo, d, h, mi = (int(m.group(i)) for i in range(1, 6))
    tz = ZoneInfo(config.ANNOUNCEMENT_TIMEZONE)
    return datetime(y, mo, d, h, mi, 0, tzinfo=tz)


async def start_announce_flow(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await message.answer(_("Access denied."))
        return
    await state.set_state(AnnounceFlow.schedule)
    await message.answer(
        _("Announce schedule prompt").format(tz=config.ANNOUNCEMENT_TIMEZONE),
    )


@router.message(Command("announce"))
async def announce_start(message: Message, state: FSMContext) -> None:
    await start_announce_flow(message, state)


@router.message(AnnounceFlow.schedule, F.text)
async def announce_schedule(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await state.clear()
        await message.answer(_("Access denied."))
        return
    try:
        when = _parse_schedule((message.text or "").strip())
    except ValueError:
        await message.answer(_("Announce schedule invalid"))
        return
    await state.update_data(scheduled_at_iso=when.isoformat())
    await state.set_state(AnnounceFlow.body)
    await message.answer(_("Announce body prompt"))


@router.message(AnnounceFlow.body, F.text)
async def announce_body(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await state.clear()
        await message.answer(_("Access denied."))
        return
    raw = (message.text or "").strip()
    if not raw:
        await message.answer(_("Announce body empty"))
        return
    data = await state.get_data()
    scheduled_iso = data.get("scheduled_at_iso")
    if not scheduled_iso:
        await state.clear()
        await message.answer(_("Announce schedule invalid"))
        return
    when = datetime.fromisoformat(scheduled_iso)
    title = _("Announce message title")
    body_lines = "<br/>".join(html.escape(line) for line in raw.splitlines())
    body_html = f"<b>{html.escape(title)}</b><br/>{body_lines}"

    async with managed_session(sessionmaker) as session:
        row = await _announce_repo.create(
            session,
            body_html=body_html,
            scheduled_at=when,
            created_by_user_id=message.from_user.id,
        )
    await state.clear()
    await message.answer(
        _("Announce scheduled ok").format(
            id=row.id,
            when=when.strftime("%Y-%m-%d %H:%M %Z"),
        ),
    )
