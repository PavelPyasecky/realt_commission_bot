from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path


DOTENV_PATH: Final = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    TELEGRAM_ACCESS_TOKEN: SecretStr

    DB_DSN: PostgresDsn

    # Business Logic
    BASIC_VALUE_BYN: int

    model_config = SettingsConfigDict(
        env_file=str(DOTENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()