from pydantic_settings import BaseSettings
from functools import lru_cache


class TokensConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"

    welcome_tokens: int = 50
    contact_open_cost: int = 5

    # Only ICO accounts can withdraw
    min_withdrawal_amount: int = 100

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> TokensConfig:
    return TokensConfig()
