from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class VayuConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "vayu-drishti"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_log_level: str = "INFO"
    app_secret_key: str = "change-me-in-production"
    app_port: int = 8000

    data_dir: str = "backend/data"
    temp_dir: str = "./tmp"

    cpcb_api_base: str = "https://app.cpcbccr.com/api"
    cpcb_api_key: str = ""
    cpcb_poll_interval_seconds: int = 900

    imd_api_base: str = "https://mausam.imd.gov.in/api"
    imd_api_key: str = ""
    imd_poll_interval_hours: int = 1

    google_maps_api_key: str = ""
    google_traffic_poll_interval_seconds: int = 300

    sentinel_client_id: str = ""
    sentinel_client_secret: str = ""
    sentinel_collection: str = "sentinel-2-l2a"

    bhuvan_api_key: str = ""
    bhuvan_api_base: str = "https://bhuvan.nrsc.gov.in/api"

    llm_model: str = "llama3-70b"
    llm_endpoint: str = "http://localhost:8001/v1"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1
    llm_context_window: int = 8192

    agent_forecast_horizon_hours: int = 72
    agent_grid_resolution_meters: int = 50
    agent_confidence_threshold: float = 0.7
    agent_cache_ttl_seconds: int = 300
    agent_max_retries: int = 3
    agent_timeout_seconds: float = 30.0

    forecast_horizon_hours: int = 72
    forecast_resolution_meters: int = 50
    forecast_cache_ttl: int = 300
    graphcast_hidden_channels: int = 128
    graphcast_num_layers: int = 12
    graphcast_model_path: str = "backend/models_data/graphcast_weights.pth"
    weather_feature_cols: list[str] = Field(default_factory=lambda: [
        "temperature", "humidity", "wind_speed", "wind_dir", "pbl_height", "precipitation"
    ])
    static_feature_cols: list[str] = Field(default_factory=lambda: [
        "elevation", "land_use", "road_density", "population", "industrial_area", "green_cover"
    ])
    temporal_fusion_hidden_dim: int = 128
    temporal_fusion_num_heads: int = 4
    temporal_fusion_dropout: float = 0.1

    rl_traffic_learning_rate: float = 0.0003
    rl_traffic_gamma: float = 0.99
    rl_squad_learning_rate: float = 0.001
    rl_emergency_alpha: float = 0.5
    traffic_light_cycle_seconds: int = 120

    feature_store_online: str = "local"
    feature_store_offline: str = "sqlite"
    feature_ttl_days: int = 90

    prometheus_port: int = 9090
    grafana_port: int = 3000

    alert_email_smtp: str = "smtp.gmail.com"
    alert_email_port: int = 587
    alert_email_user: str = ""
    alert_email_password: str = ""
    alert_slack_webhook: str = ""
    alert_pagerduty_key: str = ""

    city_lat_min: float = 28.40
    city_lat_max: float = 28.88
    city_lon_min: float = 76.84
    city_lon_max: float = 77.34
    city_grid_size_x: int = 800
    city_grid_size_y: int = 960

    @property
    def city_bounds(self) -> tuple[float, float, float, float]:
        return (self.city_lat_min, self.city_lat_max, self.city_lon_min, self.city_lon_max)

    @property
    def resolved_data_dir(self) -> str:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())

    @field_validator("cpcb_poll_interval_seconds")
    @classmethod
    def validate_poll_interval(cls, v: int) -> int:
        if v < 60:
            raise ValueError("CPCB poll interval must be at least 60 seconds")
        return v


config = VayuConfig()
