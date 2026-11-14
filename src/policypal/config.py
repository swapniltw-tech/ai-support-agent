from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: SecretStr
    anthropic_model: str
    langfuse_secret_key: SecretStr
    langfuse_public_key: SecretStr
    langfuse_base_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
