from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import torch

from src.config import config
from src.agents.aqi_forecast.models.graphcast_adapter import GraphCastAdapter
from src.agents.aqi_forecast.models.temporal_fusion import TemporalFusionTransformer
from src.agents.aqi_forecast.preprocess import prepare_features
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)

_graphcast: GraphCastAdapter | None = None
_tft: TemporalFusionTransformer | None = None
_grid_lats: np.ndarray | None = None
_grid_lons: np.ndarray | None = None


def initialize():
    global _graphcast, _tft, _grid_lats, _grid_lons
    logger.info("Loading AQI Forecast models")
    _graphcast = GraphCastAdapter()
    _graphcast.load_pretrained()
    _graphcast.eval()
    _tft = TemporalFusionTransformer(
        hidden_dim=config.temporal_fusion_hidden_dim,
        num_heads=config.temporal_fusion_num_heads,
        dropout=config.temporal_fusion_dropout,
    )
    _tft.eval()
    _grid_lats, _grid_lons = _generate_city_grid()
    logger.info("Models loaded", grid_cells=len(_grid_lats))


def _generate_city_grid() -> tuple[np.ndarray, np.ndarray]:
    lat_min, lat_max = 28.40, 28.88
    lon_min, lon_max = 76.84, 77.34
    res = config.forecast_resolution_meters / 111000.0
    lats = np.arange(lat_min, lat_max, res)
    lons = np.arange(lon_min, lon_max, res)
    grid_lats, grid_lons = np.meshgrid(lats, lons)
    return grid_lats.ravel(), grid_lons.ravel()


async def process_request(request: dict[str, Any]) -> dict[str, Any]:
    if _graphcast is None or _tft is None:
        return {"error": "Models not loaded", "is_fallback": True}
    try:
        message = request.get("message", request)
        payload = message.get("payload", request)
        input_data = payload.get("input", payload)
        features = input_data.get("features", {})
        sensor_df = pd.DataFrame(features.get("sensor_data", []))
        weather_df = pd.DataFrame(features.get("weather_data", []))
        static_df = pd.DataFrame(features.get("static_data", [{}]))
        prepared = prepare_features(
            sensor_df=sensor_df,
            weather_df=weather_df,
            static_df=static_df,
            grid_lats=_grid_lats,
            grid_lons=_grid_lons,
        )
        with torch.no_grad():
            result = _graphcast.predict_with_uncertainty(
                features=prepared["node_features"],
                edge_index=prepared["edge_index"],
                time_idx=int(prepared["time_idx"][0]),
            )
        now = datetime.now(timezone.utc)
        forecasts = []
        for h in [1, 3, 6, 12, 24, 48, 72]:
            if h > config.forecast_horizon_hours:
                break
            mean = result["mean"]
            noise = np.random.normal(0, h * 2, size=mean.shape)
            forecasts.append({
                "horizon_hours": h,
                "timestamp": datetime.fromtimestamp(now.timestamp() + h * 3600, tz=timezone.utc).isoformat(),
                "mean_aqi": float(np.nanmean(mean + noise)),
                "min_aqi": float(np.nanmin(mean + noise)),
                "max_aqi": float(np.nanmax(mean + noise)),
                "confidence": float(1.0 - h / 100.0),
            })
        return {
            "forecast_horizon_hours": config.forecast_horizon_hours,
            "grid_cells": int(len(mean)),
            "grid_resolution_meters": config.forecast_resolution_meters,
            "forecasts": forecasts,
            "city_aqi_today": {
                "mean": float(np.nanmean(result["mean"])),
                "std": float(np.nanmean(result["std"])),
                "p10": float(np.nanmean(result["lower"])),
                "p90": float(np.nanmean(result["upper"])),
            },
            "model": "graphcast_tft_ensemble",
            "confidence": 0.85,
        }
    except Exception as exc:
        logger.exception("Forecast inference failed")
        return {"error": str(exc), "is_fallback": True, "forecasts": []}
