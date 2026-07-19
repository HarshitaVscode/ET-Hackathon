from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.ml.config import MLConfig
from backend.src.ml.explainability.explainer import AQIExplainer
from backend.src.ml.models.base import BaseAQIModel


class ModelPredictor:
    def __init__(self, config: Optional[MLConfig] = None) -> None:
        self.config = config or MLConfig()
        self._model: Optional[BaseAQIModel] = None
        self._preprocessor: Optional[Any] = None
        self._feature_names: list[str] = []
        self._metadata: dict[str, Any] = {}
        self._explainer: Optional[AQIExplainer] = None

    def load(self, artifacts_dir: Optional[str] = None) -> None:
        dir_path = Path(artifacts_dir or self.config.artifacts_dir)
        model_path = dir_path / "model.pkl"
        preprocessor_path = dir_path / "preprocessor.pkl"
        metadata_path = dir_path / "metadata.json"
        features_path = dir_path / "feature_list.pkl"

        if model_path.exists():
            with open(model_path, "rb") as f:
                self._model = pickle.load(f)

        if preprocessor_path.exists():
            with open(preprocessor_path, "rb") as f:
                self._preprocessor = pickle.load(f)

        if metadata_path.exists():
            with open(metadata_path) as f:
                self._metadata = json.load(f)

        if features_path.exists():
            with open(features_path, "rb") as f:
                self._feature_names = pickle.load(f)
        else:
            self._feature_names = self._metadata.get("feature_names", [])

        if self._model is not None and self._feature_names:
            self._explainer = AQIExplainer(self._model, self._feature_names)

    def predict(self, input_data: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("No model loaded. Call load() first.")

        if self._preprocessor is not None:
            X = self._preprocessor.transform(input_data)
        else:
            missing = [c for c in self._feature_names if c not in input_data.columns]
            if missing:
                for col in missing:
                    input_data[col] = 0.0
            X = input_data[self._feature_names]

        return self._model.predict(X)

    def predict_with_explanation(self, input_data: pd.DataFrame) -> list[dict[str, Any]]:
        if self._explainer is None:
            raise RuntimeError("Explainer not available. Load model first.")
        predictions = self.predict(input_data)
        explanations: list[dict[str, Any]] = []
        for i in range(len(input_data)):
            sample = input_data.iloc[[i]]
            pred_val = float(predictions[i])
            cat = AQIExplainer._aqi_category(pred_val)
            fi = self._model.get_feature_importance() if hasattr(self._model, "get_feature_importance") else None
            explanation: dict[str, Any] = {
                "predicted_aqi": round(pred_val, 1),
                "aqi_category": cat,
                "health_advisory": AQIExplainer.get_health_advisory(cat),
            }
            if fi is not None and not fi.empty:
                top = fi.head(5)
                explanation["top_contributors"] = [
                    {"feature": row["feature"], "importance": round(float(row["importance"]), 4)}
                    for _, row in top.iterrows()
                ]
            explanations.append(explanation)
        return explanations

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    @property
    def feature_names(self) -> list[str]:
        return self._feature_names
