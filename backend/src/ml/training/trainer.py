from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from backend.src.ml.config import MLConfig
from backend.src.ml.models.base import BaseAQIModel
from backend.src.ml.training.evaluator import compute_metrics, compute_aqi_category_accuracy


def train_with_cv(
    model: BaseAQIModel,
    X: pd.DataFrame,
    y: pd.Series,
    config: Optional[MLConfig] = None,
) -> dict[str, Any]:
    cfg = config or MLConfig()
    kf = KFold(n_splits=cfg.cv_folds, shuffle=cfg.cv_shuffle, random_state=cfg.random_state)

    fold_metrics: list[dict[str, float]] = []
    fold_models: list[BaseAQIModel] = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        X_val_fold = X.iloc[val_idx]
        y_val_fold = y.iloc[val_idx]

        import copy
        fold_model = copy.deepcopy(model)
        eval_set = [(X_val_fold.values if hasattr(X_val_fold, 'values') else X_val_fold, y_val_fold.values if hasattr(y_val_fold, 'values') else y_val_fold)]
        fold_model.fit(X_train_fold, y_train_fold, eval_set=eval_set)
        preds = fold_model.predict(X_val_fold)
        metrics = compute_metrics(y_val_fold.values, preds)
        metrics["fold"] = fold + 1
        fold_metrics.append(metrics)
        fold_models.append(fold_model)

    model.fit(X, y)

    results: dict[str, Any] = {
        "fold_metrics": fold_metrics,
        "mean_metrics": {},
        "std_metrics": {},
        "model": model,
    }

    metric_keys = [k for k in fold_metrics[0] if k != "fold"]
    for key in metric_keys:
        values = [m[key] for m in fold_metrics if m.get(key) is not None]
        if values:
            results["mean_metrics"][key] = round(float(np.mean(values)), 4)
            results["std_metrics"][key] = round(float(np.std(values)), 4)

    return results


def train_test_evaluate(
    model: BaseAQIModel,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, Any]:
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    if len(preds) != len(y_test):
        y_test = y_test.iloc[-len(preds):].reset_index(drop=True)
        preds = preds[-len(y_test):]
    metrics = compute_metrics(y_test.values, preds)
    cat_acc = compute_aqi_category_accuracy(y_test.values, preds)
    return {
        "metrics": metrics,
        "category_accuracy": cat_acc,
        "predictions": preds,
        "model": model,
    }
