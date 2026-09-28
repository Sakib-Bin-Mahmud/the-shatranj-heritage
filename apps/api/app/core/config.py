from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# NFR-SEC-007 (secrets management): these fields ship with well-known
# placeholder/sample values so local dev and tests work with zero setup.
# Settings' own validator below refuses to boot in production if any of
# them are still set to these values, so a forgotten override fails
# closed at startup instead of silently running with a guessable JWT
# signing key or webhook secret.
_PRODUCTION_UNSAFE_DEFAULTS = {
    "jwt_secret_key": "change-me-in-every-environment",
    "payment_webhook_secret": "change-me-in-every-environment",
    "pathao_client_id": "change-me-in-every-environment",
    "pathao_client_secret": "change-me-in-every-environment",
    "sslcommerz_store_password": "qwerty",
    "s3_secret_key": "minioadmin",
}


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

    # The customer-facing web app. Used for payment-gateway redirect
    # targets (success/fail/cancel) — those must point at the frontend,
    # not at this API, since there's no page to redirect to here.
    frontend_base_url: str = "http://localhost:3000"

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

    # Payments — provider selection lets tests swap in a fake gateway
    # the same way S3_ENDPOINT_URL swaps in moto for storage (see
    # tests/conftest.py). "sslcommerz" is the real, network-calling
    # provider; "fake" never leaves the process.
    payment_provider: str = "sslcommerz"
    payment_webhook_secret: str = "change-me-in-every-environment"
    sslcommerz_store_id: str = "testbox"
    sslcommerz_store_password: str = "qwerty"
    sslcommerz_api_base_url: str = "https://sandbox.sslcommerz.com"
    sslcommerz_is_live: bool = False

    # Couriers (Phase 6) — same fake/real provider-selection pattern as
    # payments above. Shipping *cost* is a database-backed ShippingRate
    # lookup (BR-SHP-002), not a setting; this only configures the
    # courier-booking integration.
    courier_provider: str = "pathao"
    pathao_api_base_url: str = "https://api-hermes.pathao.com"
    pathao_client_id: str = "change-me-in-every-environment"
    pathao_client_secret: str = "change-me-in-every-environment"

    # Observability
    sentry_dsn: str | None = None
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _reject_placeholder_secrets_in_production(self) -> "Settings":
        if self.environment == "production":
            insecure = [
                name
                for name, placeholder in _PRODUCTION_UNSAFE_DEFAULTS.items()
                if getattr(self, name) == placeholder
            ]
            if insecure:
                raise ValueError(
                    "Refusing to start with ENVIRONMENT=production while these settings "
                    f"still hold their insecure sample values: {', '.join(sorted(insecure))}. "
                    "Set real values via environment variables."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
