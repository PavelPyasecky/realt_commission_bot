from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import config
from app.services import exceptions
from app.services.commission import CommissionCalculator
from app.services.input_parser import parse_amount_usd
from app.services.rounding import round_fixed
from app.services.stats import StatsService
from app.services.user_preferences import UserPreferencesService
from app.i18n import get_translator
from app.bot.keyboards import (
    build_crm_menu_keyboard,
    build_main_keyboard,
    build_result_keyboard,
    build_user_stats_keyboard,
)
from app.infrastructure.database.transaction import managed_session


router = Router()
user_preferences = UserPreferencesService()
STATS_PAGE_SIZE = 10


def _amount_to_token(amount):
    return round_fixed(amount)


def _token_to_amount(token):
    return float(token)


def _comparison_amounts(base_amount):
    return [base_amount * 0.8, base_amount, base_amount * 1.2]


def _is_admin(chat_id=None, user_id=None):
    return chat_id in config.ADMIN_ID or user_id in config.ADMIN_ID


async def _send_comparison_message(message, base_amount, _):
    lines = [f"📈 <b>{_('Comparison scenarios')}</b>"]
    for amount in _comparison_amounts(base_amount):
        calculator = await CommissionCalculator.from_amount(amount)
        lines.append(
            f"{calculator.object_usd_text} -> "
            f"<b>{calculator.tax_usd_text}</b> ({calculator.commission_text}%)"
        )
    lines.append("")
    lines.append(_("Enter new amount hint"))
    is_admin = _is_admin(
        chat_id=message.chat.id if message.chat else None,
        user_id=message.from_user.id if message.from_user else None,
    )
    await message.answer("\n".join(lines), reply_markup=build_main_keyboard(_, is_admin=is_admin))


async def _send_stats_message(message, sessionmaker, _):
    is_admin = _is_admin(
        chat_id=message.chat.id if message.chat else None,
        user_id=message.from_user.id if message.from_user else None,
    )
    if not is_admin:
        await message.answer(_("Access denied."))
        return

    text, keyboard = await _build_user_stats_response(
        sessionmaker=sessionmaker,
        _=_,
        period="day",
        page=1,
    )
    await message.answer(
        text,
        reply_markup=keyboard,
    )


async def _build_user_stats_response(sessionmaker, _, period, page):
    stats_service = StatsService()
    async with managed_session(sessionmaker) as session:
        summary = await stats_service.get_stats(session)
        page_data = await stats_service.get_users_page(
            session,
            period=period,
            page=page,
            page_size=STATS_PAGE_SIZE,
        )

    users = page_data["users"]
    period_label = _period_label(_, page_data["period"])
    lines = [
        f"<b>{_('Statistics')}</b>",
        "",
        f"DAU — {_('Active in last 24 hours')}: {summary['dau']}",
        f"WAU — {_('Active in last 7 days')}: {summary['wau']}",
        f"MAU — {_('Active in last 30 days')}: {summary['mau']}",
        f"{_('All unique')}: {summary['total']}",
        "",
        f"<b>{_('Users section title')}</b>: {period_label}",
        f"{_('Users in period')}: {page_data['total']}",
        "",
    ]
    if not users:
        lines.append(_("No users in period"))
    else:
        start_index = (page_data["page"] - 1) * STATS_PAGE_SIZE
        for idx, user in enumerate(users, start=start_index + 1):
            lines.append(_format_user_line(_, idx, user))
    text = "\n".join(lines)
    keyboard = build_user_stats_keyboard(
        _,
        period=page_data["period"],
        page=page_data["page"],
        total_pages=page_data["total_pages"],
    )
    return text, keyboard


def _format_user_line(_, idx, user):
    username = (user.username or "").strip()
    username_clean = username.lstrip("@")
    first_name = escape((user.first_name or "").strip()) or "—"
    username_display = f"@{escape(username_clean)}" if username_clean else "—"
    if username_clean:
        profile_link = f'<a href="https://t.me/{username_clean}">@{escape(username_clean)}</a>'
    else:
        profile_link = f'<a href="tg://user?id={user.tg_id}">{_("Profile link")}</a>'

    created_at = _format_dt(user.created_at)
    last_seen = _format_dt(user.last_seen)
    return (
        f"{idx}. {profile_link} | ID: <code>{user.tg_id}</code>\n"
        f"   {_('Username field')}: {username_display} | "
        f"{_('First name field')}: {first_name}\n"
        f"   {_('Created field')}: {created_at} | {_('Last seen field')}: {last_seen}"
    )


def _format_dt(dt):
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def _period_label(_, period):
    mapping = {
        "day": _("Stats period day"),
        "week": _("Stats period week"),
        "month": _("Stats period month"),
    }
    return mapping.get(period, period)


def _action_texts(_):
    return {
        _("Calculate commission"),
        _("CRM"),
        _("Last calculation"),
        _("Favorites"),
        _("Compare scenarios"),
        _("User statistics"),
    }


@router.message(Command("last"))
async def show_last_command(message):
    await _show_last_calculation(message)


@router.message(Command("favorites"))
async def show_favorites_command(message):
    await _show_favorites(message)


@router.message(Command("compare"))
async def compare_command(message):
    _ = get_translator()
    user_id = message.from_user.id
    base_amount = await user_preferences.get_last_amount(user_id)
    if base_amount is None:
        base_amount = 120000.0
    await _send_comparison_message(message, base_amount, _)


@router.message(F.text)
async def calculate(message, sessionmaker):
    _ = get_translator()
    text = (message.text or "").strip()
    is_admin = _is_admin(
        chat_id=message.chat.id if message.chat else None,
        user_id=message.from_user.id if message.from_user else None,
    )

    if text == _("Calculate commission"):
        await message.answer(
            _("Please enter the property price in USD."),
            reply_markup=build_main_keyboard(_, is_admin=is_admin),
        )
        return
    if text == _("CRM"):
        await message.answer(_("CRM"), reply_markup=build_crm_menu_keyboard(_))
        return
    if text == _("Last calculation"):
        await _show_last_calculation(message)
        return
    if text == _("Favorites"):
        await _show_favorites(message)
        return
    if text == _("Compare scenarios"):
        user_id = message.from_user.id
        base_amount = await user_preferences.get_last_amount(user_id)
        if base_amount is None:
            base_amount = 120000.0
        await _send_comparison_message(message, base_amount, _)
        return
    if text == _("User statistics"):
        await _send_stats_message(message, sessionmaker, _)
        return

    if text in _action_texts(_):
        return

    try:
        amount = parse_amount_usd(text)
        calculator = await CommissionCalculator.from_amount(amount)
    except exceptions.InputError:
        await message.answer(
            _("Input format help"),
            reply_markup=build_main_keyboard(_, is_admin=is_admin),
        )
        return
    except RuntimeError:
        await message.answer(
            _("USD rate temporarily unavailable"),
            reply_markup=build_main_keyboard(_, is_admin=is_admin),
        )
        return

    user_id = message.from_user.id
    await user_preferences.save_last_amount(user_id, amount)

    await message.answer(
        calculator.format_compact_html(),
        reply_markup=build_result_keyboard(_, _amount_to_token(amount), active_view="short"),
    )


@router.callback_query(F.data.startswith("calc:"))
async def calculation_actions(callback):
    _ = get_translator()
    payload = callback.data.split(":", maxsplit=2)

    if len(payload) == 2 and payload[1] == "new":
        is_admin = _is_admin(
            chat_id=callback.message.chat.id if callback.message and callback.message.chat else None,
            user_id=callback.from_user.id if callback.from_user else None,
        )
        await callback.message.answer(
            _("Please enter the property price in USD."),
            reply_markup=build_main_keyboard(_, is_admin=is_admin),
        )
        await callback.answer()
        return

    if len(payload) != 3:
        await callback.answer()
        return

    _prefix, action, amount_token = payload
    amount = _token_to_amount(amount_token)
    user_id = callback.from_user.id

    if action == "fav":
        await user_preferences.add_favorite_amount(user_id, amount)
        await callback.answer(_("Added to favorites"), show_alert=False)
        return

    if action == "compare":
        await _send_comparison_message(callback.message, amount, _)
        await callback.answer()
        return

    if action == "noop":
        await callback.answer()
        return

    calculator = await CommissionCalculator.from_amount(amount)
    if action == "short":
        text = calculator.format_compact_html()
        active_view = "short"
    elif action == "detailed":
        text = calculator.format_detailed_html()
        active_view = "detailed"
    else:
        await callback.answer()
        return

    await callback.message.edit_text(
        text,
        reply_markup=build_result_keyboard(_, amount_token, active_view=active_view),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ustats:"))
async def user_stats_actions(callback, sessionmaker):
    _ = get_translator()
    is_admin = _is_admin(
        chat_id=callback.message.chat.id if callback.message and callback.message.chat else None,
        user_id=callback.from_user.id if callback.from_user else None,
    )
    if not is_admin:
        await callback.answer(_("Access denied."), show_alert=True)
        return

    payload = callback.data.split(":", maxsplit=3)
    if len(payload) != 4:
        await callback.answer()
        return

    _prefix, action, period, value = payload
    if action == "noop":
        await callback.answer()
        return

    if action == "period":
        target_period = period
        target_page = 1
    elif action == "page":
        target_period = period
        try:
            target_page = int(value)
        except ValueError:
            await callback.answer()
            return
    else:
        await callback.answer()
        return

    try:
        text, keyboard = await _build_user_stats_response(
            sessionmaker=sessionmaker,
            _=_,
            period=target_period,
            page=target_page,
        )
    except ValueError:
        await callback.answer()
        return
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


async def _show_last_calculation(message):
    _ = get_translator()
    user_id = message.from_user.id
    amount = await user_preferences.get_last_amount(user_id)
    if amount is None:
        is_admin = _is_admin(
            chat_id=message.chat.id if message.chat else None,
            user_id=message.from_user.id if message.from_user else None,
        )
        await message.answer(_("No last calculation yet"), reply_markup=build_main_keyboard(_, is_admin=is_admin))
        return

    calculator = await CommissionCalculator.from_amount(amount)
    await message.answer(
        calculator.format_compact_html(),
        reply_markup=build_result_keyboard(_, _amount_to_token(amount), active_view="short"),
    )


async def _show_favorites(message):
    _ = get_translator()
    user_id = message.from_user.id
    amounts = await user_preferences.get_favorite_amounts(user_id)
    if not amounts:
        is_admin = _is_admin(
            chat_id=message.chat.id if message.chat else None,
            user_id=message.from_user.id if message.from_user else None,
        )
        await message.answer(_("No favorites yet"), reply_markup=build_main_keyboard(_, is_admin=is_admin))
        return

    lines = [f"⭐ <b>{_('Favorites')}</b>"]
    for index, amount in enumerate(amounts, start=1):
        calculator = await CommissionCalculator.from_amount(amount)
        lines.append(
            f"{index}. {calculator.object_usd_text} -> "
            f"<b>{calculator.tax_usd_text}</b> ({calculator.commission_text}%)"
        )
    lines.append("")
    lines.append(_("Enter new amount hint"))
    is_admin = _is_admin(
        chat_id=message.chat.id if message.chat else None,
        user_id=message.from_user.id if message.from_user else None,
    )
    await message.answer("\n".join(lines), reply_markup=build_main_keyboard(_, is_admin=is_admin))
