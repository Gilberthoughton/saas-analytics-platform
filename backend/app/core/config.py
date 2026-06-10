"""Application configuration via environment variables (twelve-factor)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "SaaS Analytics Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg2://analytics:analytics@localhost:5432/analytics"
    )

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_BACKEND: str = "redis"  # "redis" | "memory"
    ANALYTICS_CACHE_TTL_SECONDS: int = 30

    # CORS (comma-separated string; parsed via `cors_origins`)
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
