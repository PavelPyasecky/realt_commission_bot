import os


class Settings:
    def __init__(self):
        self.TELEGRAM_ACCESS_TOKEN = os.environ.get("TELEGRAM_ACCESS_TOKEN", "")
        self.DB_DSN = os.environ.get("DB_DSN", "")
        self.REDIS_URL = os.environ.get("REDIS_URL", "")
        self.BASIC_VALUE_BYN = float(os.environ.get("BASIC_VALUE_BYN", "0"))
        self.ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))


config = Settings()