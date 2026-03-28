from pydantic_settings import BaseSettings
from functools import lru_cache


class GatewayConfig(BaseSettings):
    auth_service_url: str = "http://auth:8001"
    users_service_url: str = "http://users:8002"
    search_service_url: str = "http://search:8003"
    tokens_service_url: str = "http://tokens:8004"
    vendors_service_url: str = "http://vendors:8005"
    gigs_service_url: str = "http://gigs:8006"
    notifications_service_url: str = "http://notifications:8007"

    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"

    # Routes that do NOT require authentication
    public_routes: list[str] = [
        "/health",
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> GatewayConfig:
    return GatewayConfig()
