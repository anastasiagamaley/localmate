from pydantic_settings import BaseSettings
from functools import lru_cache


class BaseConfig(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    redis_url: str = "redis://redis:6379/0"
    database_url: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_base_config() -> BaseConfig:
    return BaseConfig()
