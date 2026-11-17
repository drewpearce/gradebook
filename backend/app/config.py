from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Committed, public — safe only for local dev. The guard below refuses to boot with
# this value outside dev, so a forgotten override can't silently allow token forgery.
DEFAULT_SECRET_KEY = "dev-insecure-secret-change-in-production"
DEFAULT_DATABASE_URL = "postgresql+psycopg://gradebook:gradebook@localhost:5432/gradebook"


def normalize_database_url(url: str) -> str:
    """Rewrite a plain postgres(ql):// URL to the psycopg driver; leave others unchanged."""
    # Hosts (e.g. Neon) hand out plain URLs; SQLAlchemy would load psycopg2.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def alembic_url(migrations_url: str | None, app_url: str) -> str:
    """The URL Alembic connects with, escaped for its configparser.

    Prefers the schema-owner ``MIGRATIONS_DATABASE_URL``; the app role is DML-only in
    production. configparser treats "%" as interpolation (e.g. a URL-encoded password).
    """
    return normalize_database_url(migrations_url or app_url).replace("%", "%%")


class Settings(BaseSettings):
    """Application settings, read from the environment or a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["dev", "production"] = "dev"
    # Fly sets FLY_APP_NAME on every machine; used to catch a missing ENVIRONMENT.
    fly_app_name: str | None = None

    database_url: str = DEFAULT_DATABASE_URL

    # Auth. secret_key MUST be overridden outside dev (see the guard below).
    secret_key: str = DEFAULT_SECRET_KEY
    # 12 hours: covers one school day without a re-login. Kept for production (#23):
    # one teacher, and a password reset revokes every token (see the `pwd` claim).
    access_token_expire_minutes: int = 720

    # Directory of the built SPA to serve at "/" (empty = API only).
    static_dir: str = ""
    # Behind Fly's proxy, take the client IP from Fly-Client-IP (it is not spoofable there).
    trust_proxy_ip_header: bool = False

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, url: str) -> str:
        return normalize_database_url(url)

    @model_validator(mode="after")
    def _require_real_config_outside_dev(self) -> Self:
        if self.fly_app_name and self.environment != "production":
            raise ValueError("ENVIRONMENT must be 'production' on Fly")
        if self.fly_app_name and not self.trust_proxy_ip_header:
            # Otherwise every client shares the proxy's IP and one attacker locks out all.
            raise ValueError("TRUST_PROXY_IP_HEADER must be true on Fly")
        if self.environment != "dev" and self.secret_key == DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set to a non-default value when ENVIRONMENT is not 'dev' "
                "(the default is public and would let anyone forge a teacher token)."
            )
        if self.environment != "dev" and self.database_url == DEFAULT_DATABASE_URL:
            raise ValueError(
                "DATABASE_URL must be set to a non-default value when ENVIRONMENT is not 'dev'."
            )
        if self.environment == "production" and not self.static_dir:
            # Without it the app boots API-only and "/" is a 404.
            raise ValueError("STATIC_DIR must be set in production.")
        return self


settings = Settings()
