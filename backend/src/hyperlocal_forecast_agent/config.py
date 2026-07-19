from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HFConfig:
    module_dir: str = field(
        default=os.path.join(os.path.dirname(__file__))
    )
    data_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "data")
    )
    artifacts_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "artifacts")
    )
    notebooks_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "notebooks")
    )

    city: str = "Delhi"
    country: str = "IN"
    lat_min: float = 28.40
    lat_max: float = 28.90
    lon_min: float = 76.80
    lon_max: float = 77.35
    grid_size_km: float = 1.0

    forecast_horizons: list = field(default_factory=lambda: [24, 48, 72])

    walk_forward_folds: int = 5
    train_ratio: float = 0.70
    val_ratio: float = 0.15

    max_missing_hours: int = 6
    feature_max_lag: int = 72
    rolling_windows: list = field(default_factory=lambda: [6, 12, 24, 72])
    ewm_alphas: list = field(default_factory=lambda: [0.3, 0.5, 0.7])

    test_models: list = field(default_factory=lambda: [
        "RandomForest", "XGBoost", "LightGBM", "CatBoost", "LSTM", "GRU", "TFT"
    ])

    optuna_n_trials: int = 10
    lstm_epochs: int = 30
    lstm_patience: int = 5
    tft_epochs: int = 20
    tft_patience: int = 5

    openaq_api_key: Optional[str] = None
    waqi_api_token: Optional[str] = None

    seed: int = 42
