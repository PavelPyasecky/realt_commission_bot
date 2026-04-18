import re

from app.services import exceptions


_AMOUNT_PATTERN = re.compile(r"^\d+(?:[.,]\d+)?$")


def parse_amount_usd(raw_value):
    if raw_value is None:
        raise exceptions.InputError

    normalized = (
        str(raw_value)
        .strip()
        .lower()
        .replace("\u00a0", " ")
        .replace("$", "")
        .replace("usd", "")
        .replace(" ", "")
        .replace("_", "")
    )

    multiplier = 1.0
    if normalized.endswith("k"):
        multiplier = 1000.0
        normalized = normalized[:-1]

    if not normalized:
        raise exceptions.InputError

    if "," in normalized and "." in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "")
            normalized = normalized.replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif "," in normalized:
        normalized = _normalize_single_separator(normalized, ",")
    elif "." in normalized:
        normalized = _normalize_single_separator(normalized, ".")
    else:
        pass

    if not _AMOUNT_PATTERN.fullmatch(normalized):
        raise exceptions.InputError

    amount = float(normalized) * multiplier
    if amount <= 0:
        raise exceptions.InputError
    return amount


def _normalize_single_separator(value, separator):
    parts = value.split(separator)
    if len(parts) == 2:
        left, right = parts
        if len(right) == 3 and len(left) >= 1:
            return left + right
        return left + "." + right
    if len(parts) > 2:
        return "".join(parts)
    return value

