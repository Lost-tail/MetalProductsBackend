from typing import Optional

from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    SERVER_HOST: AnyHttpUrl
    POSTGRES_URL: PostgresDsn

    class Config:
        case_sensitive = True


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
