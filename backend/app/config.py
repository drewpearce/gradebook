from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from the environment or a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://gradebook:gradebook@localhost:5432/gradebook"

    # Auth. secret_key MUST be overridden in production (this default is insecure).
    secret_key: str = "dev-insecure-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720  # 12 hours

    # Origins allowed to call the API cross-origin (the Vite SPA in dev).
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
