from pydantic_settings import BaseSettings
from functools import lru_cache


class SearchConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"

    # AI provider — swap without touching business logic
    ai_provider: str = "gemini"        # gemini | openai | anthropic
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Search tuning
    max_results: int = 10
    max_distance_km: float = 50.0      # only show providers within this radius

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> SearchConfig:
    return SearchConfig()
