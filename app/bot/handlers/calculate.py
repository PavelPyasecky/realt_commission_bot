from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services import exceptions
from app.services.commission import CommissionCalculator
from app.services.input_parser import parse_amount_usd
from app.services.rounding import round_fixed
from app.services.user_preferences import UserPreferencesService
from app.i18n import get_translator
from app.bot.keyboards import build_main_keyboard, build_result_keyboard


router = Router()
user_preferences = UserPreferencesService()


def _amount_to_token(amount):
    return round_fixed(amount)


def _token_to_amount(token):
    return float(token)


def _comparison_amounts(base_amount):
    return [base_amount * 0.8, base_amount, base_amount * 1.2]


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
    await message.answer("\n".join(lines), reply_markup=build_main_keyboard(_))


def _action_texts(_):
    return {
        _("Calculate commission"),
        _("Last calculation"),
        _("Favorites"),
        _("Compare scenarios"),
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
async def calculate(message):
    _ = get_translator()
    text = (message.text or "").strip()

    if text == _("Calculate commission"):
        await message.answer(_("Please enter the property price in USD."), reply_markup=build_main_keyboard(_))
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

    if text in _action_texts(_):
        return

    try:
        amount = parse_amount_usd(text)
        calculator = await CommissionCalculator.from_amount(amount)
    except exceptions.InputError:
        await message.answer(
            _("Input format help"),
            reply_markup=build_main_keyboard(_),
        )
        return

    user_id = message.from_user.id
    await user_preferences.save_last_amount(user_id, amount)

    await message.answer(
        calculator.format_compact_html(),
        reply_markup=build_result_keyboard(_, _amount_to_token(amount)),
    )


@router.callback_query(F.data.startswith("calc:"))
async def calculation_actions(callback):
    _ = get_translator()
    payload = callback.data.split(":", maxsplit=2)

    if len(payload) == 2 and payload[1] == "new":
        await callback.message.answer(_("Please enter the property price in USD."), reply_markup=build_main_keyboard(_))
        await callback.answer()
        return

    if len(payload) != 3:
        await callback.answer()
        return

    _, action, amount_token = payload
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

    calculator = await CommissionCalculator.from_amount(amount)
    if action == "short":
        text = calculator.format_compact_html()
    else:
        text = calculator.format_detailed_html()

    await callback.message.edit_text(
        text,
        reply_markup=build_result_keyboard(_, amount_token),
    )
    await callback.answer()


async def _show_last_calculation(message):
    _ = get_translator()
    user_id = message.from_user.id
    amount = await user_preferences.get_last_amount(user_id)
    if amount is None:
        await message.answer(_("No last calculation yet"), reply_markup=build_main_keyboard(_))
        return

    calculator = await CommissionCalculator.from_amount(amount)
    await message.answer(
        calculator.format_compact_html(),
        reply_markup=build_result_keyboard(_, _amount_to_token(amount)),
    )


async def _show_favorites(message):
    _ = get_translator()
    user_id = message.from_user.id
    amounts = await user_preferences.get_favorite_amounts(user_id)
    if not amounts:
        await message.answer(_("No favorites yet"), reply_markup=build_main_keyboard(_))
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
    await message.answer("\n".join(lines), reply_markup=build_main_keyboard(_))
