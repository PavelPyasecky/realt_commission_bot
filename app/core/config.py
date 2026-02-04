import os


def _parse_admin_ids(value):
    ids = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))
    return ids


class Settings:
    def __init__(self):
        self.TELEGRAM_ACCESS_TOKEN = os.environ.get("TELEGRAM_ACCESS_TOKEN", "")
        self.DB_DSN = os.environ.get("DB_DSN", "")
        self.REDIS_URL = os.environ.get("REDIS_URL", "")
        self.BASIC_VALUE_BYN = float(os.environ.get("BASIC_VALUE_BYN", "0"))
        self.ADMIN_ID = _parse_admin_ids(os.environ.get("ADMIN_ID", ""))


config = Settings()