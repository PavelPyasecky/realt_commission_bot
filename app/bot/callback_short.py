"""Telegram callback_data must be <= 64 bytes; use compact encodings."""

_LEAD_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"

_STATUS_TO_CODE = {
    "new": "n",
    "contacted": "c",
    "meeting": "m",
    "negotiation": "g",
    "won": "w",
    "lost": "l",
    "paused": "p",
}
_CODE_TO_STATUS = {v: k for k, v in _STATUS_TO_CODE.items()}


def lead_id_to_b36(lead_id: int) -> str:
    if lead_id < 0:
        raise ValueError("lead_id must be non-negative")
    if lead_id == 0:
        return "0"
    n = lead_id
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(_LEAD_B36[r])
    return "".join(reversed(out))


def b36_to_lead_id(s: str) -> int:
    s = (s or "").strip().lower()
    if not s or any(c not in _LEAD_B36 for c in s):
        raise ValueError("invalid lead id token")
    return int(s, 36)


def status_callback(lead_id: int, status: str) -> str:
    code = _STATUS_TO_CODE.get(status)
    if code is None:
        raise ValueError(f"unknown status: {status}")
    return f"s:{lead_id_to_b36(lead_id)}:{code}"


def parse_status_callback(data: str) -> tuple[int, str]:
    parts = data.split(":", 2)
    if len(parts) != 3 or parts[0] != "s":
        raise ValueError("bad callback")
    lid = b36_to_lead_id(parts[1])
    status = _CODE_TO_STATUS.get(parts[2])
    if status is None:
        raise ValueError("bad status code")
    return lid, status


def lead_open_callback(lead_id: int) -> str:
    return f"o:{lead_id_to_b36(lead_id)}"


def parse_lead_open_callback(data: str) -> int:
    parts = data.split(":", 1)
    if len(parts) != 2 or parts[0] != "o":
        raise ValueError("bad callback")
    return b36_to_lead_id(parts[1])


def lead_only_callback(prefix: str, lead_id: int) -> str:
    if len(prefix) != 1:
        raise ValueError("prefix must be one char")
    return f"{prefix}:{lead_id_to_b36(lead_id)}"


def parse_lead_only_callback(data: str) -> tuple[str, int]:
    parts = data.split(":", 1)
    if len(parts) != 2 or len(parts[0]) != 1:
        raise ValueError("bad callback")
    return parts[0], b36_to_lead_id(parts[1])


def edit_menu_callback(kind: str, lead_id: int) -> str:
    return f"{kind}:{lead_id_to_b36(lead_id)}"


def parse_edit_menu_callback(data: str, kind: str) -> int:
    prefix, rest = data.split(":", 1)
    if prefix != kind:
        raise ValueError("bad kind")
    return b36_to_lead_id(rest)
