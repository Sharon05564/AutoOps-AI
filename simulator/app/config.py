from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulatorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "checkout-service"
    tick_interval_seconds: float = 1.0
    requests_per_tick_min: int = 40
    requests_per_tick_max: int = 120
    history_ticks: int = 900  # ~15 minutes of history at a 1s tick
    log_buffer_size: int = 6000


def get_simulator_settings() -> SimulatorSettings:
    return SimulatorSettings()
