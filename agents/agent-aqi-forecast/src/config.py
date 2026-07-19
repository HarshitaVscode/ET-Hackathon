"""AQI Forecast Agent configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ForecastConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_port: int = 8301
    app_debug: bool = True

    forecast_horizon_hours: int = 72
    forecast_resolution_meters: int = 50
    forecast_num_ensemble: int = 10
    forecast_confidence_level: float = 0.80

    graphcast_model_path: str = "./models_data/graphcast_weights.pth"
    graphcast_checkpoint_url: str = "https://storage.googleapis.com/graphcast/params_2024.nc"
    graphcast_hidden_channels: int = 256
    graphcast_num_layers: int = 12
    graphcast_mesh_size: int = 64

    temporal_fusion_hidden_dim: int = 128
    temporal_fusion_num_heads: int = 4
    temporal_fusion_dropout: float = 0.1

    feature_lag_hours: list[int] = [1, 3, 6, 12, 24, 48, 72, 168]
    weather_feature_cols: list[str] = [
        "temperature_2m", "u_component_of_wind_10m", "v_component_of_wind_10m",
        "boundary_layer_height", "relative_humidity_2m", "surface_pressure",
    ]
    static_feature_cols: list[str] = [
        "latitude", "longitude", "land_use_category",
        "population_density", "elevation", "road_density",
    ]


forecast_config = ForecastConfig()
