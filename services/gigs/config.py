from pydantic_settings import BaseSettings
from functools import lru_cache


class GigsConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"

    # Internal services
    tokens_service_url: str = "http://tokens:8004"
    users_service_url: str = "http://users:8002"
    notifications_service_url: str = "http://notifications:8007"
    worker_redis_url: str = "redis://redis:6379/0"

    # AI pricing
    gemini_api_key: str = ""
    ai_provider: str = "gemini"

    # Anti-laundering limits
    max_gig_tokens: int = 5000          # абсолютный максимум за гиг
    new_user_max_tokens: int = 500      # лимит для новых (< 5 гигов)
    new_user_gig_threshold: int = 5     # сколько гигов считается "новым"
    price_warning_multiplier: float = 3.0  # предупреждение если цена > 3x рекомендованной

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> GigsConfig:
    return GigsConfig()
