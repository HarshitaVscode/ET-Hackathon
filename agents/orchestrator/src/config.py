"""Orchestrator configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "vayu-orchestrator"
    app_env: str = "development"
    app_debug: bool = True
    app_log_level: str = "INFO"

    kafka_brokers: str = "localhost:9092"
    kafka_alert_topic: str = "alerts"
    kafka_feedback_topic: str = "feedback.aggregated"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    agent_forecast_endpoint: str = "http://agent-aqi-forecast:8301"
    agent_attribution_endpoint: str = "http://agent-source-attribution:8302"
    agent_burn_endpoint: str = "http://agent-burn-detection:8303"

    agent_confidence_threshold: float = 0.7
    agent_cache_ttl_seconds: int = 300
    agent_max_retries: int = 3
    agent_timeout_seconds: float = 30.0

    agent_configs: dict = {
        "aqi_forecast": {
            "name": "AQI Forecast Agent",
            "endpoint": "http://agent-aqi-forecast:8301",
            "timeout": 30.0,
            "max_retries": 3,
            "fallback": {"aqi_predicted": 0, "confidence": 0.0},
        },
        "source_attribution": {
            "name": "Source Attribution Agent",
            "endpoint": "http://agent-source-attribution:8302",
            "timeout": 15.0,
            "max_retries": 3,
            "fallback": {"contributions": {}, "confidence": 0.0},
        },
        "burn_detection": {
            "name": "Burn Detection Agent",
            "endpoint": "http://agent-burn-detection:8303",
            "timeout": 10.0,
            "max_retries": 2,
            "fallback": {"detections": [], "confidence": 0.0},
        },
    }

    @property
    def kafka_broker_list(self) -> list[str]:
        return [b.strip() for b in self.kafka_brokers.split(",")]


orchestrator_config = OrchestratorConfig()
