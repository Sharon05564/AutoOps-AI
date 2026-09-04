from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "AutoOps AI"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://autoops:autoops@localhost:5432/autoops"

    # Simulator
    simulator_url: str = "http://localhost:9000"

    # LLM provider
    llm_provider: str = "mock"  # mock | openai | anthropic
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # Safety / remediation policy
    safe_auto_remediation: bool = False
    max_remediation_attempts_per_incident: int = 3

    # Telemetry polling and alerting thresholds
    telemetry_poll_interval_seconds: int = 5
    error_rate_alert_threshold: float = 0.15
    latency_alert_threshold_ms: float = 800.0

    # Notifications
    slack_webhook_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
