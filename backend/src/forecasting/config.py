from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ForecastingConfig:
    artifacts_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "artifacts")
    )
    data_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "data")
    )

    n_locations: int = 10
    n_hours: int = 26280
    forecast_horizon: int = 72
    train_split: float = 0.80
    val_split: float = 0.10
    random_state: int = 42

    arima_params: dict = field(default_factory=lambda: {
        "order": (2, 1, 2),
        "seasonal_order": (1, 1, 1, 24),
        "trend": "c",
    })

    prophet_params: dict = field(default_factory=lambda: {
        "seasonality_mode": "multiplicative",
        "yearly_seasonality": True,
        "weekly_seasonality": True,
        "daily_seasonality": True,
        "changepoint_prior_scale": 0.05,
        "seasonality_prior_scale": 10.0,
    })

    lstm_params: dict = field(default_factory=lambda: {
        "seq_length": 72,
        "hidden_size": 128,
        "num_layers": 2,
        "dropout": 0.2,
        "learning_rate": 1e-3,
        "batch_size": 64,
        "epochs": 50,
        "early_stopping_patience": 10,
    })

    ensemble_params: dict = field(default_factory=lambda: {
        "weights": [0.15, 0.25, 0.60],
    })

    location_columns: list = field(default_factory=lambda: [
        "location_id", "ward", "zone", "latitude", "longitude",
    ])

    feature_columns: list = field(default_factory=lambda: [
        "AQI_lag_1", "AQI_lag_2", "AQI_lag_3", "AQI_lag_6", "AQI_lag_12", "AQI_lag_24",
        "AQI_lag_48", "AQI_lag_72",
        "AQI_rolling_mean_6", "AQI_rolling_mean_24", "AQI_rolling_mean_72",
        "AQI_rolling_max_24", "AQI_rolling_min_24",
        "AQI_hourly_diff", "AQI_daily_diff",
        "hour_sin", "hour_cos", "day_sin", "day_cos",
        "month_sin", "month_cos", "dayofweek_sin", "dayofweek_cos",
        "is_weekend", "is_rush_hour",
        "season_winter", "season_spring", "season_summer", "season_autumn",
    ])

    target_column: str = "AQI"

    aqi_breakpoints: list = field(default_factory=lambda: [
        (0, 50, "Good"),
        (51, 100, "Satisfactory"),
        (101, 200, "Moderate"),
        (201, 300, "Poor"),
        (301, 400, "Very Poor"),
        (401, 500, "Severe"),
    ])
