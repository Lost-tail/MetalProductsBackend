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

    class Config:
        case_sensitive = True
        extra = "ignore"


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
