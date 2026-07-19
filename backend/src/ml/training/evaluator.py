from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    n = len(y_true)
    p = 1
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2

    mask = y_true > 0
    mape_val: Optional[float] = None
    if mask.sum() > 0:
        mape_val = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    return {
        "MAE": round(mae, 3),
        "MSE": round(mse, 3),
        "RMSE": round(rmse, 3),
        "R2": round(r2, 4),
        "Adjusted_R2": round(adj_r2, 4),
        "MAPE": round(mape_val, 2) if mape_val is not None else None,
    }


def compute_aqi_category_accuracy(
    y_true: np.ndarray, y_pred: np.ndarray,
) -> dict[str, Any]:
    def _category(aqi: float) -> str:
        if aqi <= 50:
            return "Good"
        if aqi <= 100:
            return "Satisfactory"
        if aqi <= 200:
            return "Moderate"
        if aqi <= 300:
            return "Poor"
        if aqi <= 400:
            return "Very Poor"
        return "Severe"

    cats_true = [_category(v) for v in y_true]
    cats_pred = [_category(v) for v in y_pred]
    correct = sum(1 for a, b in zip(cats_true, cats_pred) if a == b)
    total = len(cats_true)
    return {
        "category_accuracy": round(correct / total * 100, 2) if total > 0 else 0.0,
        "correct": correct,
        "total": total,
    }
