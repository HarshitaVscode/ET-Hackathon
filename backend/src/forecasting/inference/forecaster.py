from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.forecasting.config import ForecastingConfig
from backend.src.forecasting.features.builder import build_features
from backend.src.forecasting.models.base import BaseForecastModel
from backend.src.forecasting.models.arima_model import ARIMAForecast
from backend.src.forecasting.models.prophet_model import ProphetForecast
from backend.src.forecasting.models.lstm_forecaster import LSTMHorizonForecast
from backend.src.forecasting.models.ensemble import ForecastEnsemble


class Forecaster:
    def __init__(self, config: Optional[ForecastingConfig] = None) -> None:
        self.config = config or ForecastingConfig()
        self._models: dict[int, BaseForecastModel] = {}
        self._location_metadata: dict[int, dict] = {}
        self._feature_cols: list[str] = []
        self._metadata: dict[str, Any] = {}

    def load(self, artifacts_dir: Optional[str] = None) -> None:
        d = Path(artifacts_dir or self.config.artifacts_dir)
        models_dir = d / "models"
        if models_dir.exists():
            for p in models_dir.glob("location_*.pkl"):
                loc_id = int(p.stem.split("_")[1])
                with open(p, "rb") as f:
                    self._models[loc_id] = pickle.load(f)

        meta_path = d / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                self._metadata = json.load(f)
            self._feature_cols = self._metadata.get("feature_columns", [])
            loc_meta = self._metadata.get("location_metadata", {})
            self._location_metadata = {int(k): v for k, v in loc_meta.items()}

    def predict_location(self, location_id: int, steps: int, history_df: Optional[pd.DataFrame] = None) -> dict[str, Any]:
        if location_id not in self._models:
            return {"error": f"Location {location_id} not found"}

        model = self._models[location_id]
        X_future = None
        if history_df is not None and self._feature_cols:
            df_feat = build_features(history_df)
            df_feat = df_feat.dropna().reset_index(drop=True)
            if len(df_feat) > 0 and all(c in df_feat.columns for c in self._feature_cols):
                X_future = df_feat[self._feature_cols]

        preds = model.predict(steps, X_future)
        cat = self._aqi_category(float(preds[-1]) if len(preds) > 0 else 0)
        meta = self._location_metadata.get(location_id, {})
        return {
            "location_id": location_id,
            "ward": meta.get("ward", ""),
            "zone": meta.get("zone", ""),
            "forecast": np.round(preds, 1).tolist(),
            "steps": steps,
            "latest_aqi": float(preds[-1]) if len(preds) > 0 else None,
            "category": cat,
            "model": model.name,
        }

    def predict_all(self, steps: int) -> list[dict[str, Any]]:
        results = []
        for loc_id in sorted(self._models.keys()):
            results.append(self.predict_location(loc_id, steps))
        return results

    @staticmethod
    def _aqi_category(v: float) -> str:
        if v <= 50: return "Good"
        if v <= 100: return "Satisfactory"
        if v <= 200: return "Moderate"
        if v <= 300: return "Poor"
        if v <= 400: return "Very Poor"
        return "Severe"

    @property
    def is_loaded(self) -> bool:
        return len(self._models) > 0
