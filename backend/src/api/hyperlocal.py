from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()

_forecaster: Optional[object] = None


def get_forecaster():
    global _forecaster
    if _forecaster is None:
        from backend.src.forecasting.inference.forecaster import Forecaster
        from backend.src.forecasting.config import ForecastingConfig
        cfg = ForecastingConfig()
        _forecaster = Forecaster(cfg)
        _forecaster.load()
    return _forecaster


@router.get("/hyperlocal/locations")
async def list_locations() -> list[dict]:
    f = get_forecaster()
    if not f.is_loaded:
        raise HTTPException(status_code=503, detail="Forecaster not loaded")
    return [
        {"location_id": lid, **meta}
        for lid, meta in f._location_metadata.items()
    ]


@router.get("/hyperlocal/forecast/{location_id}")
async def get_forecast(location_id: int, steps: int = 72) -> dict:
    f = get_forecaster()
    if not f.is_loaded:
        raise HTTPException(status_code=503, detail="Forecaster not loaded")
    result = f.predict_location(location_id, steps)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hyperlocal/forecast/all")
async def get_all_forecasts(steps: int = 72) -> list[dict]:
    f = get_forecaster()
    if not f.is_loaded:
        raise HTTPException(status_code=503, detail="Forecaster not loaded")
    return f.predict_all(steps)
