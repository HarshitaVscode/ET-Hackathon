from __future__ import annotations

import time
import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from backend.src.hyperlocal_forecast_agent.config import HFConfig
from backend.src.hyperlocal_forecast_agent.models.base import BaseForecastModel

warnings.filterwarnings("ignore")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute all evaluation metrics."""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt = y_true[mask]
    yp = y_pred[mask]
    n = len(yt)
    if n == 0:
        return {"MAE": np.nan, "MSE": np.nan, "RMSE": np.nan, "MAPE": np.nan, "sMAPE": np.nan, "R2": np.nan, "Adj_R2": np.nan}

    mae = float(np.mean(np.abs(yt - yp)))
    mse = float(np.mean((yt - yp) ** 2))
    rmse = float(np.sqrt(mse))
    mape = float(np.mean(np.abs((yt - yp) / (np.abs(yt) + 1e-8)))) * 100
    smape = float(100 * np.mean(2 * np.abs(yt - yp) / (np.abs(yt) + np.abs(yp) + 1e-8)))
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    r2 = float(1 - ss_res / (ss_tot + 1e-10))
    p = 1  # number of predictors beyond constant
    adj_r2 = float(1 - (1 - r2) * (n - 1) / (n - p - 1)) if n > p + 1 else r2

    return {
        "MAE": round(mae, 4),
        "MSE": round(mse, 4),
        "RMSE": round(rmse, 4),
        "MAPE": round(mape, 4),
        "sMAPE": round(smape, 4),
        "R2": round(r2, 4),
        "Adj_R2": round(adj_r2, 4),
    }


def walk_forward_validation(
    model: BaseForecastModel,
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "aqi",
    n_splits: int = 5,
    horizon: int = 72,
) -> dict[str, Any]:
    """Walk-Forward TimeSeriesSplit validation.

    Each fold trains on past data and predicts `horizon` steps ahead.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_results = []
    all_preds = []
    all_actuals = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(df)):
        train_df = df.iloc[train_idx].reset_index(drop=True)
        test_df = df.iloc[test_idx].reset_index(drop=True)

        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        test_horizon = min(horizon, len(test_df))
        X_test = test_df[feature_cols].iloc[:test_horizon]
        y_test = test_df[target_col].iloc[:test_horizon].values

        if len(X_train) < 10 or len(X_test) < 1:
            continue

        m = model.__class__.__name__
        try:
            model_clone = _clone_model(model, X_train.shape[1])
            eval_set = [(X_test, y_test)]
            model_clone.fit(X_train, y_train, eval_set=eval_set)
            preds = model_clone.predict(X_test)
        except Exception as e:
            print(f"  Fold {fold + 1} failed: {e}")
            continue

        metrics = compute_metrics(y_test, preds)
        metrics["fold"] = fold + 1
        metrics["train_size"] = len(X_train)
        metrics["test_size"] = len(X_test)
        fold_results.append(metrics)
        all_preds.extend(preds.tolist())
        all_actuals.extend(y_test.tolist())

    if not fold_results:
        return {"error": "All folds failed"}

    summary = {}
    for key in ["MAE", "MSE", "RMSE", "MAPE", "sMAPE", "R2", "Adj_R2"]:
        vals = [r[key] for r in fold_results]
        summary[f"mean_{key}"] = round(float(np.mean(vals)), 4)
        summary[f"std_{key}"] = round(float(np.std(vals)), 4)

    summary["fold_results"] = fold_results
    summary["n_folds"] = len(fold_results)
    summary["predictions"] = all_preds
    summary["actuals"] = all_actuals
    return summary


def train_test_evaluate(
    model: BaseForecastModel,
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "aqi",
    train_ratio: float = 0.7,
    horizon: int = 72,
    cat_features: Optional[list] = None,
) -> dict[str, Any]:
    """Simple train/test split evaluation."""
    split = int(len(df) * train_ratio)
    train_df = df.iloc[:split]
    test_df = df.iloc[split:]

    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    test_horizon = min(horizon, len(test_df))
    X_test = test_df[feature_cols].iloc[:test_horizon]
    y_test = test_df[target_col].iloc[:test_horizon].values

    t0 = time.time()
    kwargs = {}
    if cat_features and hasattr(model, "_model") and "cat_features" in model._model.__class__.__name__.lower():
        kwargs["cat_features"] = cat_features
    eval_set = [(X_test, y_test)]
    model.fit(X_train, y_train, eval_set=eval_set, **kwargs)
    train_time = time.time() - t0

    t0 = time.time()
    preds = model.predict(X_test)
    infer_time = time.time() - t0

    metrics = compute_metrics(y_test, preds)
    metrics["train_time_s"] = round(train_time, 2)
    metrics["infer_time_ms"] = round(infer_time * 1000, 2)

    fi = model.get_feature_importance()
    return {
        "metrics": metrics,
        "predictions": preds.tolist(),
        "actuals": y_test.tolist(),
        "feature_importance": fi.to_dict("records") if fi is not None else None,
    }


def _clone_model(model: BaseForecastModel, n_features: int) -> BaseForecastModel:
    """Create a fresh instance of the same model class."""
    import copy
    try:
        return copy.deepcopy(model)
    except Exception:
        cls = model.__class__
        new = cls()
        return new
