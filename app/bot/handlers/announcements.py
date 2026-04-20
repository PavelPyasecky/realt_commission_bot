from __future__ import annotations

import html
import re
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from zoneinfo import ZoneInfo

from app.bot.keyboards.broadcast import (
    build_broadcast_detail_keyboard,
    build_broadcast_home_keyboard,
    build_broadcast_list_keyboard,
)
from app.core.config import config
from app.infrastructure.database.transaction import managed_session
from app.infrastructure.repositories.announcement_repository import AnnouncementRepository
from app.i18n import get_translator

router = Router()
_repo = AnnouncementRepository()
_LIST_PAGE = 8

_DATETIME_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*$")


class BroadcastFlow(StatesGroup):
    schedule = State()
    body = State()
    edit_schedule = State()
    edit_body = State()


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


def _build_body_html(_, raw: str) -> tuple[str, str]:
    title = _("Announce message title")
    plain = raw.strip()
    body_lines = "<br/>".join(html.escape(line) for line in plain.splitlines())
    body_html = f"<b>{html.escape(title)}</b><br/>{body_lines}"
    return body_html, plain


def _row_title(row) -> str:
    if row.body_plain:
        line = row.body_plain.strip().splitlines()[0] if row.body_plain.strip() else ""
        return line[:80] or f"#{row.id}"
    return f"#{row.id}"


async def _render_detail(callback: CallbackQuery, sessionmaker, aid: int) -> None:
    _ = get_translator()
    async with managed_session(sessionmaker) as session:
        row = await _repo.get_by_id(session, aid)
    if row is None or not callback.message:
        return
    when = row.scheduled_at.strftime("%Y-%m-%d %H:%M %Z")
    sent = row.sent_at.strftime("%Y-%m-%d %H:%M %Z") if row.sent_at else "—"
    err = (row.error_message or "—")[:500]
    preview = html.escape((row.body_plain or "")[:800] or "")
    text = (
        f"<b>{_('Broadcast detail title')} #{row.id}</b>\n"
        f"{_('Broadcast field state')}: {row.state}\n"
        f"{_('Broadcast field schedule')}: {when}\n"
        f"{_('Broadcast field sent')}: {sent}\n"
        f"{_('Broadcast field error')}: {html.escape(err)}\n\n"
        f"<b>{_('Broadcast field preview')}</b>\n{preview}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=build_broadcast_detail_keyboard(_, row.id, row.state),
    )


async def open_broadcast_menu(message: Message, state: FSMContext | None = None) -> None:
    _ = get_translator()
    if state is not None:
        await state.clear()
    await message.answer(_("Broadcast menu title"), reply_markup=build_broadcast_home_keyboard(_))


async def start_new_broadcast(message: Message, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await message.answer(_("Access denied."))
        return
    await state.set_state(BroadcastFlow.schedule)
    await message.answer(_("Announce schedule prompt").format(tz=config.ANNOUNCEMENT_TIMEZONE))


@router.message(Command("announce"))
async def cmd_announce(message: Message, state: FSMContext) -> None:
    await open_broadcast_menu(message, state)


@router.callback_query(F.data == "bc:h")
async def bc_home(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    await state.clear()
    if callback.message:
        await callback.message.edit_text(_("Broadcast menu title"), reply_markup=build_broadcast_home_keyboard(_))
    await callback.answer()


@router.callback_query(F.data == "bc:x")
async def bc_close(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data == "bc:add")
async def bc_add(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    await state.set_state(BroadcastFlow.schedule)
    if callback.message:
        await callback.message.answer(_("Announce schedule prompt").format(tz=config.ANNOUNCEMENT_TIMEZONE))
    await callback.answer()


def _list_page_from_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    return parts[1][1], int(parts[2])


@router.callback_query(F.data.startswith("bc:lp:"))
async def bc_list_pending(callback: CallbackQuery, sessionmaker) -> None:
    await _bc_list_page(callback, sessionmaker, "pending", "p")


@router.callback_query(F.data.startswith("bc:lf:"))
async def bc_list_failed(callback: CallbackQuery, sessionmaker) -> None:
    await _bc_list_page(callback, sessionmaker, "failed", "f")


@router.callback_query(F.data.startswith("bc:ls:"))
async def bc_list_sent(callback: CallbackQuery, sessionmaker) -> None:
    await _bc_list_page(callback, sessionmaker, "sent", "s")


async def _bc_list_page(callback: CallbackQuery, sessionmaker, state: str, kind_char: str) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    _, page = _list_page_from_callback(callback.data)
    offset = page * _LIST_PAGE
    async with managed_session(sessionmaker) as session:
        total = await _repo.count_by_state(session, state=state)
        rows_db = await _repo.list_by_state(session, state=state, limit=_LIST_PAGE + 1, offset=offset)
    has_more = len(rows_db) > _LIST_PAGE
    slice_rows = rows_db[:_LIST_PAGE]
    list_rows = [(r.id, _row_title(r)) for r in slice_rows]
    titles = {
        "pending": _("Broadcast list pending"),
        "failed": _("Broadcast list failed"),
        "sent": _("Broadcast list sent"),
    }
    header = f"{titles[state]} ({total})\n"
    if callback.message:
        await callback.message.edit_text(
            header + _("Broadcast list hint"),
            reply_markup=build_broadcast_list_keyboard(_, list_rows, kind_char, page, has_more),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("bc:v:"))
async def bc_view(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    aid = int(callback.data.split(":")[2])
    async with managed_session(sessionmaker) as session:
        row = await _repo.get_by_id(session, aid)
    if row is None:
        await callback.answer(_("Broadcast not found"), show_alert=True)
        return
    if not callback.message:
        await callback.answer()
        return
    when = row.scheduled_at.strftime("%Y-%m-%d %H:%M %Z")
    sent = row.sent_at.strftime("%Y-%m-%d %H:%M %Z") if row.sent_at else "—"
    err = (row.error_message or "—")[:500]
    preview = html.escape((row.body_plain or "")[:800] or "")
    text = (
        f"<b>{_('Broadcast detail title')} #{row.id}</b>\n"
        f"{_('Broadcast field state')}: {row.state}\n"
        f"{_('Broadcast field schedule')}: {when}\n"
        f"{_('Broadcast field sent')}: {sent}\n"
        f"{_('Broadcast field error')}: {html.escape(err)}\n\n"
        f"<b>{_('Broadcast field preview')}</b>\n{preview}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=build_broadcast_detail_keyboard(_, row.id, row.state),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bc:cn:"))
async def bc_cancel(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    aid = int(callback.data.split(":")[2])
    async with managed_session(sessionmaker) as session:
        ok = await _repo.cancel(session, aid)
    await callback.answer(_("Broadcast cancelled ok") if ok else _("Broadcast cancel failed"), show_alert=True)
    if ok:
        await _render_detail(callback, sessionmaker, aid)


@router.callback_query(F.data.startswith("bc:dl:"))
async def bc_delete(callback: CallbackQuery, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    aid = int(callback.data.split(":")[2])
    async with managed_session(sessionmaker) as session:
        ok = await _repo.delete(session, aid)
    await callback.answer(_("Broadcast deleted ok") if ok else _("Broadcast delete failed"), show_alert=True)
    if ok and callback.message:
        await callback.message.edit_text(_("Broadcast menu title"), reply_markup=build_broadcast_home_keyboard(_))


@router.callback_query(F.data.startswith("bc:es:"))
async def bc_edit_schedule_start(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    aid = int(callback.data.split(":")[2])
    await state.set_state(BroadcastFlow.edit_schedule)
    await state.update_data(edit_announcement_id=aid)
    if callback.message:
        await callback.message.answer(
            _("Broadcast edit schedule prompt").format(tz=config.ANNOUNCEMENT_TIMEZONE),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("bc:eb:"))
async def bc_edit_body_start(callback: CallbackQuery, state: FSMContext) -> None:
    _ = get_translator()
    if not _is_admin(callback.from_user.id if callback.from_user else None, callback.message.chat.id if callback.message else None):
        await callback.answer(_("Access denied."), show_alert=True)
        return
    aid = int(callback.data.split(":")[2])
    await state.set_state(BroadcastFlow.edit_body)
    await state.update_data(edit_announcement_id=aid)
    if callback.message:
        await callback.message.answer(_("Announce body prompt"))
    await callback.answer()


@router.message(BroadcastFlow.schedule, F.text)
async def on_schedule(message: Message, state: FSMContext) -> None:
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
    await state.set_state(BroadcastFlow.body)
    await message.answer(_("Announce body prompt"))


@router.message(BroadcastFlow.body, F.text)
async def on_body(message: Message, state: FSMContext, sessionmaker) -> None:
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
    body_html, plain = _build_body_html(_, raw)
    async with managed_session(sessionmaker) as session:
        row = await _repo.create(
            session,
            body_html=body_html,
            body_plain=plain,
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


@router.message(BroadcastFlow.edit_schedule, F.text)
async def on_edit_schedule(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await state.clear()
        await message.answer(_("Access denied."))
        return
    aid = (await state.get_data()).get("edit_announcement_id")
    if not aid:
        await state.clear()
        await message.answer(_("Broadcast not found"))
        return
    try:
        when = _parse_schedule((message.text or "").strip())
    except ValueError:
        await message.answer(_("Announce schedule invalid"))
        return
    async with managed_session(sessionmaker) as session:
        ok = await _repo.update_schedule(session, int(aid), when)
    await state.clear()
    await message.answer(_("Broadcast schedule updated") if ok else _("Broadcast update failed"))


@router.message(BroadcastFlow.edit_body, F.text)
async def on_edit_body(message: Message, state: FSMContext, sessionmaker) -> None:
    _ = get_translator()
    if not _is_admin(message.from_user.id if message.from_user else None, message.chat.id if message.chat else None):
        await state.clear()
        await message.answer(_("Access denied."))
        return
    aid = (await state.get_data()).get("edit_announcement_id")
    raw = (message.text or "").strip()
    if not aid or not raw:
        await message.answer(_("Announce body empty"))
        return
    body_html, plain = _build_body_html(_, raw)
    async with managed_session(sessionmaker) as session:
        ok = await _repo.update_body(session, int(aid), body_html=body_html, body_plain=plain)
    await state.clear()
    await message.answer(_("Broadcast body updated") if ok else _("Broadcast update failed"))
