from pydantic import PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TELEGRAM_ACCESS_TOKEN: SecretStr

    DB_DSN: PostgresDsn


    REDIS_URL: RedisDsn

    # Business Logic
    BASIC_VALUE_BYN: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()