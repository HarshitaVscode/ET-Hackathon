from __future__ import annotations

import json
import os
import pickle
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from backend.src.ml.config import MLConfig
from backend.src.ml.data.loader import AQIDatasetLoader
from backend.src.ml.models.xgboost_model import XGBoostAQIModel
from backend.src.ml.models.random_forest import RandomForestAQIModel
from backend.src.ml.models.lstm_model import LSTMAQIModel
from backend.src.ml.models.ensemble import StackingEnsemble
from backend.src.ml.training.evaluator import compute_metrics, compute_aqi_category_accuracy
from backend.src.ml.training.trainer import train_test_evaluate


def run_training(quick_mode: bool = True) -> dict[str, Any]:
    config = MLConfig()
    if quick_mode:
        config.n_synthetic_samples = 10_000
        config.xgboost_params["n_estimators"] = 100
        config.random_forest_params["n_estimators"] = 100
        config.lstm_params["epochs"] = 30
        config.lstm_params["seq_length"] = 12
        config.lstm_params["hidden_size"] = 64

    print("Loading dataset...")
    loader = AQIDatasetLoader(config)
    df = loader.load_or_generate(force_generate=True)
    print(f"Dataset shape: {df.shape}")

    feature_cols = (
        config.polluntant_columns
        + config.meteorological_columns
        + config.temporal_columns
    )
    available_cols = [c for c in feature_cols if c in df.columns]
    print(f"Using {len(available_cols)} features: {available_cols}")

    X = df[available_cols]
    y = df[config.target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=config.random_state
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15 / 0.85, random_state=config.random_state
    )
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=available_cols, index=X_train.index
    )
    X_val_scaled = pd.DataFrame(
        scaler.transform(X_val), columns=available_cols, index=X_val.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=available_cols, index=X_test.index
    )

    categorical_cols = ["Hour", "Day", "Month", "DayOfWeek", "Season"]
    for col in categorical_cols:
        if col in available_cols:
            X_train_scaled[col] = X_train[col].values
            X_val_scaled[col] = X_val[col].values
            X_test_scaled[col] = X_test[col].values

    print("\n--- Training XGBoost ---")
    xgb_model = XGBoostAQIModel(config)
    xgb_result = train_test_evaluate(
        xgb_model, X_train_scaled, y_train, X_test_scaled, y_test
    )
    print(f"XGBoost Test RMSE: {xgb_result['metrics']['RMSE']}, R2: {xgb_result['metrics']['R2']}")

    print("\n--- Training Random Forest ---")
    rf_model = RandomForestAQIModel(config)
    rf_result = train_test_evaluate(
        rf_model, X_train_scaled, y_train, X_test_scaled, y_test
    )
    print(f"Random Forest Test RMSE: {rf_result['metrics']['RMSE']}, R2: {rf_result['metrics']['R2']}")

    print("\n--- Training LSTM ---")
    lstm_model = LSTMAQIModel(config)
    lstm_result = train_test_evaluate(
        lstm_model, X_train_scaled, y_train, X_test_scaled, y_test
    )
    print(f"LSTM Test RMSE: {lstm_result['metrics']['RMSE']}, R2: {lstm_result['metrics']['R2']}")

    print("\n--- Training Stacking Ensemble ---")
    ensemble = StackingEnsemble([xgb_model, rf_model, lstm_model])
    ensemble_result = train_test_evaluate(
        ensemble, X_train_scaled, y_train, X_test_scaled, y_test
    )
    print(f"Ensemble Test RMSE: {ensemble_result['metrics']['RMSE']}, R2: {ensemble_result['metrics']['R2']}")

    best_model = ensemble
    best_metrics = ensemble_result["metrics"]
    best_cat = compute_aqi_category_accuracy(y_test.values, ensemble.predict(X_test_scaled))

    print(f"\nBest Model: Ensemble")
    print(f"RMSE: {best_metrics['RMSE']}")
    print(f"R2: {best_metrics['R2']}")
    print(f"MAE: {best_metrics['MAE']}")
    print(f"MAPE: {best_metrics.get('MAPE', 'N/A')}")
    print(f"Category Accuracy: {best_cat['category_accuracy']}%")

    print("\n--- Saving Artifacts ---")
    artifacts_dir = Path(config.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with open(artifacts_dir / "model.pkl", "wb") as f:
        pickle.dump(best_model, f)

    with open(artifacts_dir / "preprocessor.pkl", "wb") as f:
        pickle.dump(scaler, f)

    with open(artifacts_dir / "feature_list.pkl", "wb") as f:
        pickle.dump(available_cols, f)

    metadata = {
        "model_name": "StackingEnsemble",
        "base_models": ["XGBoost", "RandomForest", "LSTM"],
        "feature_names": available_cols,
        "target": "AQI",
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "metrics": {k: v for k, v in best_metrics.items() if v is not None},
        "category_accuracy": best_cat["category_accuracy"],
        "aqi_breakpoints": config.aqi_breakpoints,
    }
    with open(artifacts_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Artifacts saved to {artifacts_dir}")
    return {
        "config": config,
        "models": {
            "xgboost": xgb_result,
            "random_forest": rf_result,
            "lstm": lstm_result,
            "ensemble": ensemble_result,
        },
        "best_model": best_model,
        "best_metrics": best_metrics,
        "feature_names": available_cols,
        "X_test": X_test_scaled,
        "y_test": y_test,
    }


if __name__ == "__main__":
    quick = "--full" not in sys.argv
    if not quick:
        print("Running FULL training mode...")
    result = run_training(quick_mode=quick)
    print("\nTraining complete!")
