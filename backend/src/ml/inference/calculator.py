from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from backend.src.ml.config import MLConfig
from backend.src.ml.explainability.explainer import AQIExplainer
from backend.src.ml.inference.predictor import ModelPredictor


class AQICalculator:
    def __init__(self, predictor: ModelPredictor) -> None:
        self.predictor = predictor
        self.feature_names = predictor.feature_names

    def predict_from_dict(self, input_values: dict[str, float]) -> dict[str, Any]:
        row: dict[str, float] = {}
        for feature in self.feature_names:
            row[feature] = input_values.get(feature, 0.0)
        df = pd.DataFrame([row])
        result = self.predictor.predict_with_explanation(df)
        return result[0] if result else {"error": "Prediction failed"}

    def get_input_schema(self) -> list[dict[str, Any]]:
        schema: list[dict[str, Any]] = []
        for name in self.feature_names:
            entry: dict[str, Any] = {"name": name}
            if any(p in name for p in ["PM2_5", "PM10", "NO", "NO2", "SO2", "CO", "O3", "NH3", "Benzene", "Toluene", "Xylene"]):
                entry["type"] = "pollutant"
                entry["unit"] = "µg/m³"
                entry["min"] = 0.0
                entry["max"] = 500.0
                entry["default"] = 50.0
            elif name in ["Temperature"]:
                entry["type"] = "meteorological"
                entry["unit"] = "°C"
                entry["min"] = 0.0
                entry["max"] = 50.0
                entry["default"] = 25.0
            elif name in ["Humidity"]:
                entry["type"] = "meteorological"
                entry["unit"] = "%"
                entry["min"] = 0.0
                entry["max"] = 100.0
                entry["default"] = 60.0
            elif name in ["Wind_Speed"]:
                entry["type"] = "meteorological"
                entry["unit"] = "m/s"
                entry["min"] = 0.0
                entry["max"] = 20.0
                entry["default"] = 3.0
            elif name in ["Wind_Direction"]:
                entry["type"] = "meteorological"
                entry["unit"] = "degrees"
                entry["min"] = 0.0
                entry["max"] = 360.0
                entry["default"] = 180.0
            elif name in ["Pressure"]:
                entry["type"] = "meteorological"
                entry["unit"] = "hPa"
                entry["min"] = 950.0
                entry["max"] = 1050.0
                entry["default"] = 1013.0
            elif name in ["Rainfall"]:
                entry["type"] = "meteorological"
                entry["unit"] = "mm"
                entry["min"] = 0.0
                entry["max"] = 100.0
                entry["default"] = 0.0
            elif name in ["Visibility"]:
                entry["type"] = "meteorological"
                entry["unit"] = "km"
                entry["min"] = 0.0
                entry["max"] = 20.0
                entry["default"] = 10.0
            elif name in ["Hour", "Day", "Month", "DayOfWeek", "Season"]:
                entry["type"] = "temporal"
                entry["unit"] = ""
                entry["min"] = 0
                entry["max"] = 23 if name == "Hour" else 12 if name == "Month" else 6 if name == "DayOfWeek" else 3 if name == "Season" else 31
                entry["default"] = 12 if name == "Hour" else 1
            else:
                entry["type"] = "other"
                entry["unit"] = ""
                entry["min"] = 0.0
                entry["max"] = 1000.0
                entry["default"] = 0.0
            schema.append(entry)
        return schema

    def batch_predict(self, inputs: list[dict[str, float]]) -> list[dict[str, Any]]:
        return [self.predict_from_dict(inp) for inp in inputs]
