import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN") or os.getenv("TELEGRAM_ACCESS_TOKEN")

NBRB_BASE_URL = "https://api.nbrb.by/exrates/"

BASIC_VALUE_IN_BYN = os.getenv("BASIC_VALUE_IN_BYN") or os.getenv("BASIC_VALUE_BYN")

CONNECTION_TIMEOUT = float(os.getenv("CONNECTION_TIMEOUT", 3))


def normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql+asyncpg://"):
        return value.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


CRM_DATABASE_URL = normalize_database_url(
    os.getenv("CRM_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("DB_DSN")
    or "sqlite:///data/crm.sqlite3"
)
CRM_TIMEZONE = os.getenv("CRM_TIMEZONE", "UTC")
