"""API Gateway configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewayConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8000
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production"

    orchestrator_url: str = "http://agent-orchestrator:8300"
    knowledge_graph_url: str = "http://knowledge-graph:8100"
    decision_engine_url: str = "http://decision-engine:8400"
    llm_service_url: str = "http://llm-service:8500"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    rate_limit_per_minute: int = 60
    token_expiry_hours: int = 24


gateway_config = GatewayConfig()
