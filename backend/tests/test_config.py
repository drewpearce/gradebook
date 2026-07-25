import pytest
from pydantic import ValidationError

from app.config import DEFAULT_SECRET_KEY, Settings


def test_default_secret_is_rejected_outside_dev() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", secret_key=DEFAULT_SECRET_KEY)


def test_default_secret_is_allowed_in_dev() -> None:
    settings = Settings(environment="dev", secret_key=DEFAULT_SECRET_KEY)
    assert settings.secret_key == DEFAULT_SECRET_KEY


def test_real_secret_is_accepted_outside_dev() -> None:
    settings = Settings(environment="production", secret_key="a-real-secret-of-sufficient-length!!")
    assert settings.environment == "production"
