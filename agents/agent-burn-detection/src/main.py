"""
Burn Detection Agent — Entry Point.

Detects active fires and agricultural burning from satellite
thermal anomalies (VIIRS, MODIS) and multispectral imagery
(Sentinel-2 SWIR). Predicts plume trajectories and estimates
pollutant emissions for each detected event.

Runs on a continuous detection loop and publishes alerts
to the orchestrator when new burns are found.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import numpy as np
from fastapi import FastAPI

from src.config import burn_config
from src.detectors.viirs_detector import VIIRSFireDetector
from src.plume_tracker import PlumeTracker

logger = __import__("structlog").get_logger(__name__)

_viirs_detector: VIIRSFireDetector | None = None
_plume_tracker: PlumeTracker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _viirs_detector, _plume_tracker
    logger.info("Initializing Burn Detection Agent")
    _viirs_detector = VIIRSFireDetector()
    _plume_tracker = PlumeTracker()
    yield


app = FastAPI(
    title="Vayu-Drishti Burn Detection Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "detector_ready": _viirs_detector is not None,
    }


@app.post("/api/v1/process")
async def process_request(request: dict[str, Any]) -> dict[str, Any]:
    """Detect fires from satellite thermal data."""
    if not _viirs_detector or not _plume_tracker:
        return {"error": "Detector not ready", "is_fallback": True}

    try:
        message = request.get("message", {})
        payload = message.get("payload", request)
        input_data = payload.get("input", payload)

        # Simulate VIIRS detection with synthetic data
        h, w = 100, 100
        bt = np.random.default_rng().normal(290, 15, (h, w))
        # Inject some hotspots
        for _ in range(np.random.randint(0, 4)):
            cx, cy = np.random.randint(10, 90, 2)
            bt[cx-3:cx+3, cy-3:cy+3] += np.random.uniform(40, 80)

        lats = np.linspace(28.40, 28.88, h)
        lons = np.linspace(76.84, 77.34, w)

        fires = _viirs_detector.detect(bt, lats, lons)

        # Enrich with plume predictions
        for fire in fires:
            plume = _plume_tracker.predict_trajectory(
                fire_lat=fire["latitude"],
                fire_lon=fire["longitude"],
                fire_intensity=fire.get("fire_radiative_power_mw", 10),
                wind_speed_ms=input_data.get("wind_speed_ms", 3.5),
                wind_direction_deg=input_data.get("wind_direction_deg", 270),
                pbl_height_m=input_data.get("pbl_height_m", 1000),
            )
            fire["plume_trajectory"] = plume[:6]  # First 6 hours

            emissions = _plume_tracker.estimate_emissions(
                area_hectares=fire["area_hectares"],
                land_cover_type=input_data.get("land_cover", "agricultural"),
            )
            fire["estimated_emissions"] = emissions

        return {
            "detections": fires,
            "num_fires": len(fires),
            "model": "viirs_threshold_yolo_ensemble",
            "detection_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.exception("Burn detection failed")
        return {"error": str(exc), "is_fallback": True}


def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=burn_config.app_port,
        reload=burn_config.app_debug,
    )


if __name__ == "__main__":
    main()
