from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from environment variables / .env.

    Every module reads config through this object rather than calling
    `os.environ` directly, so all runtime configuration stays discoverable
    in one place.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General
    app_name: str = "The Shatranj Heritage API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_allow_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://shatranj:shatranj@localhost:5432/shatranj_heritage"

    # Cache
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible; MinIO in local dev)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "shatranj-heritage"

    # Auth
    jwt_secret_key: str = "change-me-in-every-environment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Observability
    sentry_dsn: str | None = None
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
