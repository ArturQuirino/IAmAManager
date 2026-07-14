import re
from datetime import timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_jwt_expires_in(value: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([dhms])", value.strip())
    if not match:
        raise ValueError(f"Invalid JWT_EXPIRES_IN format: {value}")

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "d":
        return timedelta(days=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    return timedelta(seconds=amount)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "football_manager"
    postgres_user: str = "fm_user"
    postgres_password: str = "fm_password"
    # Required by managed Postgres providers that mandate TLS (e.g. Neon).
    # Empty by default so local/Docker Compose connections are unaffected.
    postgres_sslmode: str = ""

    jwt_secret: str = "local_dev_secret_change_in_production"
    jwt_expires_in: str = "7d"

    app_env: str = "development"
    run_seed: str = "false"
    cors_origins: str = "http://localhost:3000"

    # Daily matchday job: whether the in-process scheduler runs, and the local
    # wall-clock time it fires each day (see docs/competition.md — 18:00).
    scheduler_enabled: str = "false"
    matchday_hour: int = 18
    matchday_minute: int = 0

    @property
    def database_url(self) -> str:
        base = (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.postgres_sslmode:
            return f"{base}?sslmode={self.postgres_sslmode}"
        return base

    @property
    def jwt_expires_delta(self) -> timedelta:
        return parse_jwt_expires_in(self.jwt_expires_in)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def should_seed(self) -> bool:
        return self.run_seed.lower() == "true" or self.app_env == "development"

    @property
    def is_scheduler_enabled(self) -> bool:
        return self.scheduler_enabled.lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
