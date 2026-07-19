from __future__ import annotations

from typing import Any, Optional

from backend.src.forecasting.inference.forecaster import Forecaster
from backend.src.forecasting.config import ForecastingConfig


_forecaster: Optional[Forecaster] = None


def initialize(artifacts_dir: Optional[str] = None) -> None:
    global _forecaster
    cfg = ForecastingConfig()
    if artifacts_dir:
        cfg.artifacts_dir = artifacts_dir
    _forecaster = Forecaster(cfg)
    _forecaster.load()
    print(f"Hyperlocal AQI Forecaster initialized (locations: {len(_forecaster._models)})")


def process_request(payload: dict[str, Any]) -> dict[str, Any]:
    if _forecaster is None:
        return {"error": "Forecaster not initialized. Call initialize() first."}
    location_id = payload.get("location_id")
    steps = payload.get("steps", 72)
    if location_id is not None:
        return _forecaster.predict_location(int(location_id), steps)
    return {"locations": _forecaster.predict_all(steps)}
