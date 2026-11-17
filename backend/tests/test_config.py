import pytest
from pydantic import ValidationError

from app.config import DEFAULT_DATABASE_URL, DEFAULT_SECRET_KEY, Settings

REAL_SECRET = "a-real-secret-of-sufficient-length!!"
REAL_DB = "postgresql+psycopg://u:p@db.example/gradebook"
STATIC = "/app/static"


def test_default_secret_is_rejected_outside_dev() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", secret_key=DEFAULT_SECRET_KEY)


def test_default_secret_is_allowed_in_dev() -> None:
    settings = Settings(environment="dev", secret_key=DEFAULT_SECRET_KEY)
    assert settings.secret_key == DEFAULT_SECRET_KEY


def test_real_secret_is_accepted_outside_dev() -> None:
    settings = Settings(
        environment="production", secret_key=REAL_SECRET, database_url=REAL_DB, static_dir=STATIC
    )
    assert settings.environment == "production"


@pytest.mark.parametrize("prefix", ["postgres://", "postgresql://"])
def test_plain_postgres_url_is_rewritten_to_psycopg(prefix: str) -> None:
    settings = Settings(database_url=f"{prefix}u:p@host/db")
    assert settings.database_url == "postgresql+psycopg://u:p@host/db"


def test_psycopg_url_is_left_unchanged() -> None:
    url = "postgresql+psycopg://u:p@host/db"
    assert Settings(database_url=url).database_url == url


def test_default_database_url_is_rejected_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production", secret_key=REAL_SECRET, database_url=DEFAULT_DATABASE_URL
        )


def test_fly_requires_production_environment() -> None:
    with pytest.raises(ValidationError, match="ENVIRONMENT must be 'production' on Fly"):
        Settings(environment="dev", fly_app_name="gradebook")
    settings = Settings(
        environment="production",
        fly_app_name="gradebook",
        secret_key=REAL_SECRET,
        database_url=REAL_DB,
        static_dir=STATIC,
        trust_proxy_ip_header=True,
    )
    assert settings.fly_app_name == "gradebook"


def test_fly_requires_trusting_the_proxy_ip_header() -> None:
    # Without it every client shares Fly's proxy IP, so one attacker locks everyone out.
    with pytest.raises(ValidationError, match="TRUST_PROXY_IP_HEADER"):
        Settings(
            environment="production",
            fly_app_name="gradebook",
            secret_key=REAL_SECRET,
            database_url=REAL_DB,
        )


def test_production_requires_static_dir() -> None:
    with pytest.raises(ValidationError, match="STATIC_DIR"):
        Settings(environment="production", secret_key=REAL_SECRET, database_url=REAL_DB)
