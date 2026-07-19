from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
import optuna
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor

from backend.src.ml.config import MLConfig


def _objective_xgboost(
    trial: optuna.Trial,
    X: pd.DataFrame,
    y: pd.Series,
    cv_folds: int,
    random_state: int,
) -> float:
    params: dict[str, Any] = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.3, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
        "random_state": random_state,
        "verbosity": 0,
    }
    model = XGBRegressor(**params, objective="reg:squarederror")
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring="neg_root_mean_squared_error")
    return float(scores.mean())


def _objective_random_forest(
    trial: optuna.Trial,
    X: pd.DataFrame,
    y: pd.Series,
    cv_folds: int,
    random_state: int,
) -> float:
    params: dict[str, Any] = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000, step=50),
        "max_depth": trial.suggest_int("max_depth", 5, 30),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
        "bootstrap": trial.suggest_categorical("bootstrap", [True, False]),
        "random_state": random_state,
        "n_jobs": -1,
    }
    model = RandomForestRegressor(**params)
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring="neg_root_mean_squared_error")
    return float(scores.mean())


def tune_xgboost(
    X: pd.DataFrame,
    y: pd.Series,
    config: Optional[MLConfig] = None,
) -> dict[str, Any]:
    cfg = config or MLConfig()
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=cfg.random_state),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(
        lambda trial: _objective_xgboost(trial, X, y, cfg.cv_folds, cfg.random_state),
        n_trials=cfg.n_trials_optuna,
        timeout=cfg.optuna_timeout_minutes * 60 if cfg.optuna_timeout_minutes else None,
        show_progress_bar=False,
    )
    return study.best_params


def tune_random_forest(
    X: pd.DataFrame,
    y: pd.Series,
    config: Optional[MLConfig] = None,
) -> dict[str, Any]:
    cfg = config or MLConfig()
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=cfg.random_state),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(
        lambda trial: _objective_random_forest(trial, X, y, cfg.cv_folds, cfg.random_state),
        n_trials=cfg.n_trials_optuna,
        timeout=cfg.optuna_timeout_minutes * 60 if cfg.optuna_timeout_minutes else None,
        show_progress_bar=False,
    )
    return study.best_params
