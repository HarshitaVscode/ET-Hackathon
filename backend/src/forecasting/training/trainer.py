from __future__ import annotations

import time
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.forecasting.config import ForecastingConfig
from backend.src.forecasting.features.builder import build_features
from backend.src.forecasting.models.base import BaseForecastModel
from backend.src.forecasting.training.evaluator import compute_forecast_metrics


def train_location(
    model: BaseForecastModel,
    df_loc: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "AQI",
    forecast_horizon: int = 72,
) -> dict[str, Any]:
    df_feat = build_features(df_loc)
    df_feat = df_feat.dropna().reset_index(drop=True)

    split = int(len(df_feat) * 0.8)
    train = df_feat.iloc[:split]
    test = df_feat.iloc[split:]

    X_train = train[feature_cols]
    y_train = train[target_col]

    loc_id = int(df_loc["location_id"].iloc[0])
    model.fit(loc_id, X_train, y_train)

    test_X = test[feature_cols]
    test_y = test[target_col].values

    if len(test_X) < forecast_horizon:
        preds = model.predict(len(test_X), test_X)
    else:
        preds = model.predict(forecast_horizon, test_X.iloc[:forecast_horizon])
        test_y = test_y[:forecast_horizon]

    if len(preds) > len(test_y):
        preds = preds[:len(test_y)]
    elif len(preds) < len(test_y):
        test_y = test_y[:len(preds)]

    metrics = compute_forecast_metrics(test_y, preds)
    return {
        "metrics": metrics,
        "predictions": preds,
        "actual": test_y,
        "train_size": len(train),
        "test_size": len(test),
    }


def train_all_locations(
    model: BaseForecastModel,
    df: pd.DataFrame,
    config: ForecastingConfig,
) -> dict[int, dict[str, Any]]:
    results: dict[int, dict[str, Any]] = {}
    for loc_id, grp in df.groupby("location_id"):
        grp = grp.sort_values("datetime").reset_index(drop=True)
        t0 = time.time()
        result = train_location(model, grp, config.feature_columns, config.target_column, config.forecast_horizon)
        elapsed = time.time() - t0
        result["training_time"] = round(elapsed, 2)
        results[int(loc_id)] = result
        print(f"  Location {int(loc_id)}: RMSE={result['metrics']['RMSE']}, R2={result['metrics']['R2']} ({elapsed:.1f}s)")
    return results


def summarize_results(all_results: dict[str, dict[int, dict]], n_locations: int) -> pd.DataFrame:
    rows = []
    for model_name, loc_results in all_results.items():
        rmse_vals = [r["metrics"]["RMSE"] for r in loc_results.values()]
        r2_vals = [r["metrics"]["R2"] for r in loc_results.values()]
        time_vals = [r.get("training_time", 0) for r in loc_results.values()]
        rows.append({
            "Model": model_name,
            "Mean_RMSE": round(float(np.mean(rmse_vals)), 3),
            "Std_RMSE": round(float(np.std(rmse_vals)), 3),
            "Mean_R2": round(float(np.mean(r2_vals)), 4),
            "Std_R2": round(float(np.std(r2_vals)), 4),
            "Total_Time_s": round(sum(time_vals), 1),
        })
    return pd.DataFrame(rows).sort_values("Mean_RMSE")
