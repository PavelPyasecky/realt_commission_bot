import os


def _parse_admin_ids(value):
    ids = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))
    return ids


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql+asyncpg://"):
        return value.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class Settings:
    def __init__(self):
        self.TELEGRAM_ACCESS_TOKEN = os.environ.get("TELEGRAM_ACCESS_TOKEN") or os.environ.get("ACCESS_TOKEN", "")
        self.DB_DSN = _normalize_database_url(
            os.environ.get("DB_DSN")
            or os.environ.get("DATABASE_URL")
            or os.environ.get("CRM_DATABASE_URL")
            or ""
        )
        self.REDIS_URL = os.environ.get("REDIS_URL", "")
        self.BASIC_VALUE_BYN = float(os.environ.get("BASIC_VALUE_BYN", "0"))
        self.ADMIN_ID = _parse_admin_ids(os.environ.get("ADMIN_ID", ""))


config = Settings()