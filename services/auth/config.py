from pydantic_settings import BaseSettings
from functools import lru_cache


class AuthConfig(BaseSettings):
    # DB
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"

    # JWT
    secret_key: str = "change_this_to_a_long_random_string_min_32_chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Services
    tokens_service_url: str = "http://tokens:8004"
    users_service_url: str = "http://users:8002"

    # Token economy
    welcome_tokens: int = 50

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # App
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> AuthConfig:
    return AuthConfig()
