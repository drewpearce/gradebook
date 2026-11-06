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


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://"])
def test_plain_postgres_url_is_rewritten_to_psycopg(prefix: str) -> None:
    settings = Settings(database_url=f"{prefix}u:p@host/db")
    assert settings.database_url == "postgresql+psycopg://u:p@host/db"


def test_psycopg_url_is_left_unchanged() -> None:
    url = "postgresql+psycopg://u:p@host/db"
    assert Settings(database_url=url).database_url == url
