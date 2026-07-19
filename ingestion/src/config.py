"""
Application configuration for Vayu-Drishti ingestion layer.

Uses pydantic-settings to load from environment variables with
sensible defaults for local development. All secrets and endpoints
are configurable via .env file or environment variables.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "vayu-drishti-ingestion"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_log_level: str = "INFO"

    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_satellite_topic: str = "raw.satellite"
    kafka_sensor_topic: str = "raw.sensor"
    kafka_weather_topic: str = "raw.weather"
    kafka_traffic_topic: str = "raw.traffic"
    kafka_citizen_topic: str = "raw.citizen"
    kafka_alert_topic: str = "alerts"
    kafka_consumer_group: str = "vayu-ingestion"
    kafka_partitions: int = 6
    kafka_replication: int = 1

    # APIs
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

    # Object storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "vayu_minio"
    minio_secret_key: str = "vayu_minio_secret"
    minio_bucket_satellite: str = "vayu-satellite"
    minio_bucket_reports: str = "vayu-reports"

    # Data paths
    data_dir: str = "./data"
    temp_dir: str = "./tmp"

    # City boundaries (default: Delhi)
    city_lat_min: float = 28.40
    city_lat_max: float = 28.88
    city_lon_min: float = 76.84
    city_lon_max: float = 77.34

    @property
    def kafka_broker_list(self) -> list[str]:
        return [b.strip() for b in self.kafka_brokers.split(",")]

    @property
    def city_bounds(self) -> tuple[float, float, float, float]:
        return (self.city_lat_min, self.city_lat_max, self.city_lon_min, self.city_lon_max)

    @field_validator("cpcb_poll_interval_seconds")
    @classmethod
    def validate_poll_interval(cls, v: int) -> int:
        if v < 60:
            raise ValueError("CPCB poll interval must be at least 60 seconds")
        return v

    @field_validator("data_dir")
    @classmethod
    def resolve_data_dir(cls, v: str) -> str:
        p = Path(v)
        p.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())


config = IngestionConfig()
