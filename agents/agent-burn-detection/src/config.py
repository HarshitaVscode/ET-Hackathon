"""Burn Detection Agent configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BurnConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8303
    app_debug: bool = True

    yolo_model_path: str = "./models/yolo_nas_burn.pt"
    yolo_confidence_threshold: float = 0.5
    yolo_iou_threshold: float = 0.45
    yolo_input_size: int = 640

    viirs_fire_confidence_threshold: float = 0.7
    modis_fire_confidence_threshold: float = 0.6

    plume_tracker_horizon_hours: int = 48
    min_burn_area_hectares: float = 0.1
    detection_frequency_minutes: int = 15


burn_config = BurnConfig()
