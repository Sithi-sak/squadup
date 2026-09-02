from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    cors_origins: list[str] = ["http://localhost:5173"]

    supabase_url: str
    supabase_service_role_key: str

    stripe_secret_key: str

    # Platform's cut of a completed booking, tracked per-booking only - no escrow, no coins
    # actually move for it (recap_squadup.md's "commission tracked manually", CHECKPOINT 4.3).
    platform_commission_pct: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
