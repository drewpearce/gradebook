from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Committed, public — safe only for local dev. The guard below refuses to boot with
# this value outside dev, so a forgotten override can't silently allow token forgery.
DEFAULT_SECRET_KEY = "dev-insecure-secret-change-in-production"


class Settings(BaseSettings):
    """Application settings, read from the environment or a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "dev"

    database_url: str = "postgresql+psycopg://gradebook:gradebook@localhost:5432/gradebook"

    # Auth. secret_key MUST be overridden outside dev (see the guard below).
    secret_key: str = DEFAULT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720  # 12 hours

    # Origins allowed to call the API cross-origin (the Vite SPA in dev).
    cors_origins: list[str] = ["http://localhost:5173"]

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> Self:
        if self.environment != "dev" and self.secret_key == DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be set to a non-default value when ENVIRONMENT is not 'dev' "
                "(the default is public and would let anyone forge a teacher token)."
            )
        return self


settings = Settings()
