from pydantic_settings import BaseSettings
from functools import lru_cache


class UsersConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"

    # XP per completed gig
    xp_per_gig: int = 10

    # Level thresholds (gigs completed)
    level_bronze_min: int = 0
    level_silver_min: int = 10
    level_gold_min: int = 30
    level_platinum_min: int = 100
    level_master_min: int = 300

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> UsersConfig:
    return UsersConfig()
