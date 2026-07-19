from __future__ import annotations

from typing import Optional

import numpy as np


def compute_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    mse = float(np.mean((y_true - y_pred) ** 2))
    rmse = float(np.sqrt(mse))
    sse = float(np.sum((y_true - y_pred) ** 2))
    sst = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - sse / sst if sst > 0 else 0.0

    n = len(y_true)
    p = 1
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2

    mask = np.abs(y_true) > 0
    smape: Optional[float] = None
    if mask.sum() > 0:
        smape_val = 2.0 * np.mean(np.abs(y_true[mask] - y_pred[mask]) / (np.abs(y_true[mask]) + np.abs(y_pred[mask])) + 1e-10)
        smape = round(float(smape_val) * 100, 2)

    naive_errors = np.abs(np.diff(y_true))
    if len(naive_errors) > 0 and not np.all(naive_errors == 0):
        mase = float(np.mean(np.abs(y_true - y_pred)) / np.mean(naive_errors))
    else:
        mase = float(mae / np.std(y_true)) if np.std(y_true) > 0 else 0.0

    return {
        "MAE": round(mae, 3),
        "MSE": round(mse, 3),
        "RMSE": round(rmse, 3),
        "R2": round(r2, 4),
        "Adjusted_R2": round(adj_r2, 4),
        "sMAPE": smape,
        "MASE": round(mase, 4),
    }


def aqi_category_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    def _cat(v: float) -> str:
        if v <= 50: return "Good"
        if v <= 100: return "Satisfactory"
        if v <= 200: return "Moderate"
        if v <= 300: return "Poor"
        if v <= 400: return "Very Poor"
        return "Severe"

    correct = sum(1 for a, b in zip(y_true, y_pred) if _cat(a) == _cat(b))
    return {"accuracy": round(correct / len(y_true) * 100, 2) if len(y_true) > 0 else 0.0,
            "correct": correct, "total": len(y_true)}
