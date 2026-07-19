"""Decision Engine configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class DecisionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8400
    app_debug: bool = True

    rl_traffic_learning_rate: float = 0.0003
    rl_traffic_gamma: float = 0.99
    rl_squad_learning_rate: float = 0.001
    rl_emergency_alpha: float = 0.5

    emergency_response_max_minutes: int = 30
    enforcement_queue_max_items: int = 100
    traffic_light_cycle_seconds: int = 120


decision_config = DecisionConfig()
