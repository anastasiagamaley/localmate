from pydantic_settings import BaseSettings
from functools import lru_cache


class NotificationsConfig(BaseSettings):
    # Resend
    resend_api_key: str = ""
    from_email: str = "noreply@localmate.sk"
    from_name: str = "LocalMate"

    # App
    app_url: str = "http://localhost:3000"
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> NotificationsConfig:
    return NotificationsConfig()
