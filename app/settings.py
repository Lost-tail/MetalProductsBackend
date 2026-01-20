from typing import Optional

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    SERVER_HOST: AnyHttpUrl
    POSTGRES_URL: PostgresDsn
    REDIS_URL: RedisDsn
    YANDEX_DELIVERY_API_KEY: str = ""
    TG_BOT_KEY: str = ""
    TG_CHAT_ID: str = ""
    TG_LOG_CHAT_ID: str = ""
    DEBUG: bool = False
    PAYKEEPER_USER: str = ""
    PAYKEEPER_PASSWORD: str = ""
    PAYKEEPER_SECRET: str = ""


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
