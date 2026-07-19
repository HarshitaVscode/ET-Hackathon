from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MLConfig:
    artifacts_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "artifacts")
    )
    data_dir: str = field(
        default=os.path.join(os.path.dirname(__file__), "data")
    )

    n_synthetic_samples: int = 50_000
    train_split: float = 0.70
    val_split: float = 0.15
    random_state: int = 42

    cv_folds: int = 5
    cv_shuffle: bool = True

    n_trials_optuna: int = 50
    optuna_timeout_minutes: Optional[float] = None

    xgboost_params: dict = field(default_factory=lambda: {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "early_stopping_rounds": 30,
        "random_state": 42,
    })

    random_forest_params: dict = field(default_factory=lambda: {
        "n_estimators": 500,
        "max_depth": 20,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "bootstrap": True,
        "oob_score": True,
        "random_state": 42,
        "n_jobs": -1,
    })

    lstm_params: dict = field(default_factory=lambda: {
        "seq_length": 24,
        "hidden_size": 128,
        "num_layers": 2,
        "dropout": 0.2,
        "learning_rate": 1e-3,
        "batch_size": 64,
        "epochs": 100,
        "early_stopping_patience": 15,
    })

    polluntant_columns: list = field(default_factory=lambda: [
        "PM2_5", "PM10", "NO", "NO2", "SO2", "CO", "O3", "NH3",
        "Benzene", "Toluene", "Xylene",
    ])

    meteorological_columns: list = field(default_factory=lambda: [
        "Temperature", "Humidity", "Wind_Speed", "Wind_Direction",
        "Pressure", "Rainfall", "Visibility",
    ])

    temporal_columns: list = field(default_factory=lambda: [
        "Hour", "Day", "Month", "DayOfWeek", "Season",
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
