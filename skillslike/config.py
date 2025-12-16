"""Configuration management for SkillsLike."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Load from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    anthropic_api_key: str = ""
    anthropic_base_url: str | None = None

    # OpenAI compatibility (for third-party providers)
    openai_api_key: str = ""
    openai_base_url: str | None = None
    use_openai_compatible: bool = False

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "skillslike"

    # Application
    skills_dir: Path = Path("skills/")
    file_store_dir: Path = Path("data/files/")
    checkpoint_store: str = "memory"  # memory, redis, sqlite

    # Executor
    docker_enabled: bool = False
    executor_timeout: int = 300

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Routing
    max_tools_per_request: int = 5
    router_match_threshold: float = 0.0

    def validate_paths(self) -> None:
        """Ensure required directories exist."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.file_store_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings.

    Returns:
        Settings instance.
    """
    return settings
