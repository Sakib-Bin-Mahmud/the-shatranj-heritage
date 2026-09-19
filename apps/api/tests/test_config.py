import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_boots_with_placeholder_secrets() -> None:
    Settings(environment="development")


def test_production_rejects_placeholder_secrets() -> None:
    with pytest.raises(ValidationError, match="insecure sample values"):
        Settings(environment="production")


def test_production_boots_once_secrets_are_overridden() -> None:
    Settings(
        environment="production",
        jwt_secret_key="a-real-random-signing-key",
        payment_webhook_secret="a-real-webhook-secret",
        pathao_client_id="real-client-id",
        pathao_client_secret="real-client-secret",
        sslcommerz_store_password="real-store-password",
        s3_secret_key="real-s3-secret",
    )
