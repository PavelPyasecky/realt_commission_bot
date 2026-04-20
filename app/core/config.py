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
        self.BOT_MODE = (os.environ.get("BOT_MODE") or os.environ.get("TELEGRAM_MODE") or "polling").strip().lower()
        self.WEBHOOK_URL = (os.environ.get("WEBHOOK_URL") or "").strip()
        self.WEBHOOK_BASE_URL = (os.environ.get("WEBHOOK_BASE_URL") or "").strip().rstrip("/")
        self.WEBHOOK_PATH = (os.environ.get("WEBHOOK_PATH") or "/webhook").strip()
        self.WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
        self.WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8080"))
        self.WEBHOOK_SECRET_TOKEN = (os.environ.get("WEBHOOK_SECRET_TOKEN") or "").strip() or None
        self.WEBHOOK_HANDLE_IN_BACKGROUND = os.environ.get("WEBHOOK_HANDLE_IN_BACKGROUND", "1") not in ("0", "false", "False")
        self.WEBHOOK_DROP_PENDING_ON_SET = os.environ.get("WEBHOOK_DROP_PENDING_ON_SET", "0") in ("1", "true", "True")
        self.WEBHOOK_DELETE_ON_SHUTDOWN = os.environ.get("WEBHOOK_DELETE_ON_SHUTDOWN", "1") not in ("0", "false", "False")
        self.REMINDER_DELIVERY_INTERVAL_SECONDS = float(os.environ.get("REMINDER_DELIVERY_INTERVAL_SECONDS", "30"))
        self.REMINDER_DELIVERY_BATCH = int(os.environ.get("REMINDER_DELIVERY_BATCH", "25"))

    def webhook_public_url(self) -> str:
        if self.WEBHOOK_URL:
            return self.WEBHOOK_URL.rstrip("/")
        if self.WEBHOOK_BASE_URL:
            path = self.WEBHOOK_PATH if self.WEBHOOK_PATH.startswith("/") else f"/{self.WEBHOOK_PATH}"
            return f"{self.WEBHOOK_BASE_URL}{path}"
        return ""


config = Settings()