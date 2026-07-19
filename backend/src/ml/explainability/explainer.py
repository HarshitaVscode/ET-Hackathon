from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.ml.models.base import BaseAQIModel


class AQIExplainer:
    def __init__(self, model: BaseAQIModel, feature_names: list[str]) -> None:
        self.model = model
        self.feature_names = feature_names

    def explain_prediction(self, X_sample: pd.DataFrame) -> dict[str, Any]:
        prediction = float(self.model.predict(X_sample)[0])
        feature_importance = self.model.get_feature_importance()

        if feature_importance is not None and not feature_importance.empty:
            top_features = feature_importance.head(5)
            contributions: dict[str, float] = {}
            for _, row in top_features.iterrows():
                contributions[str(row["feature"])] = round(float(row["importance"]), 4)
        else:
            contributions = {}

        return {
            "predicted_aqi": round(prediction, 1),
            "aqi_category": self._aqi_category(prediction),
            "feature_contributions": contributions,
            "top_features": list(contributions.keys()),
        }

    def batch_explain(self, X: pd.DataFrame) -> list[dict[str, Any]]:
        return [self.explain_prediction(X.iloc[[i]]) for i in range(len(X))]

    @staticmethod
    def _aqi_category(aqi: float) -> str:
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

    @staticmethod
    def get_health_advisory(category: str) -> str:
        advisories = {
            "Good": "Air quality is satisfactory. No health risks.",
            "Satisfactory": "Minor discomfort for sensitive individuals.",
            "Moderate": "May cause breathing discomfort for sensitive groups.",
            "Poor": "May cause breathing discomfort on prolonged exposure.",
            "Very Poor": "May cause respiratory illness on prolonged exposure.",
            "Severe": "May cause respiratory effects even on brief exposure.",
        }
        return advisories.get(category, "Unknown category.")
