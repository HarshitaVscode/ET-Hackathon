from __future__ import annotations

import json
import pickle
import warnings
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.hyperlocal_forecast_agent.config import HFConfig
from backend.src.hyperlocal_forecast_agent.data.feature_engineering import FeatureEngineer

warnings.filterwarnings("ignore")


class ForecastInference:
    """Load trained forecasting artifacts and generate predictions without retraining."""

    def __init__(self, config: Optional[HFConfig] = None) -> None:
        self.cfg = config or HFConfig()
        self._model: Any = None
        self._feature_cols: list[str] = []
        self._target_col: str = "aqi"
        self._metadata: dict = {}
        self.is_loaded: bool = False

    def load(self, artifacts_dir: Optional[str] = None) -> None:
        d = Path(artifacts_dir or self.cfg.artifacts_dir)
        model_path = d / "model.pkl"
        meta_path = d / "metadata.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")

        with open(model_path, "rb") as f:
            self._model = pickle.load(f)

        if meta_path.exists():
            with open(meta_path) as f:
                self._metadata = json.load(f)
            self._feature_cols = self._metadata.get("feature_columns", [])
            self._target_col = self._metadata.get("target_column", "aqi")

        self.is_loaded = True
        print(f"  Model loaded: {type(self._model).__name__}")
        print(f"  Features: {len(self._feature_cols)}")
        print(f"  Metadata: {self._metadata.get('best_model', 'unknown')}")

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        if not self.is_loaded or self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        missing = [c for c in self._feature_cols if c not in features.columns]
        if missing:
            for c in missing:
                features[c] = 0
        return self._model.predict(features[self._feature_cols])

    def aqi_category(self, v: float) -> str:
        if v <= 50: return "Good"
        if v <= 100: return "Satisfactory"
        if v <= 200: return "Moderate"
        if v <= 300: return "Poor"
        if v <= 400: return "Very Poor"
        return "Severe"

    def forecast_horizon(self, df: pd.DataFrame, steps: int = 72) -> dict[str, Any]:
        """Generate forecast for next `steps` hours."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        fe = FeatureEngineer(self.cfg, self._target_col)
        fe._feature_cols = self._feature_cols

        last_features = df[self._feature_cols].iloc[-1:].copy()
        predictions = []
        confidences = []
        current_df = df.copy()

        for i in range(steps):
            feat = fe._build_all(current_df)
            if self._feature_cols:
                if all(c in feat.columns for c in self._feature_cols):
                    X = feat[self._feature_cols].iloc[-1:].fillna(0)
                    pred = self.predict(X)[0]
                else:
                    pred = current_df[self._target_col].iloc[-1] if self._target_col in current_df.columns else 150
            else:
                pred = current_df[self._target_col].iloc[-1] if self._target_col in current_df.columns else 150

            pred = max(0, min(500, pred))
            predictions.append(float(round(pred, 1)))
            conf = max(50, 95 - i * 0.5)
            confidences.append(round(conf, 1))

            new_row = {self._target_col: pred}
            if "datetime" in current_df.columns:
                new_row["datetime"] = pd.Timestamp(current_df["datetime"].iloc[-1]) + pd.Timedelta(hours=1)
            new_df = pd.DataFrame([new_row])
            for c in current_df.columns:
                if c not in new_df.columns:
                    new_df[c] = current_df[c].iloc[-1] if c != self._target_col else pred
            current_df = pd.concat([current_df, new_df], ignore_index=True).tail(200)

        return {
            "forecast": predictions,
            "confidence": confidences,
            "steps": steps,
            "latest_aqi": predictions[-1] if predictions else None,
            "category": self.aqi_category(predictions[-1]) if predictions else "Unknown",
        }
