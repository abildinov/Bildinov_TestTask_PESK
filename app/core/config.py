from functools import lru_cache
from pydantic import SecretStr
from pydantic.networks import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    debug: bool = True

    pg_dsn: PostgresDsn
    redis_dsn: RedisDsn

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()