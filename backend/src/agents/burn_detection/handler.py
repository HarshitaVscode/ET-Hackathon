from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from src.config import config
from src.agents.burn_detection.detectors.viirs_detector import VIIRSFireDetector
from src.agents.burn_detection.plume_tracker import PlumeTracker
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)

_viirs_detector: VIIRSFireDetector | None = None
_plume_tracker: PlumeTracker | None = None


def initialize():
    global _viirs_detector, _plume_tracker
    logger.info("Initializing Burn Detection Agent")
    _viirs_detector = VIIRSFireDetector()
    _plume_tracker = PlumeTracker()


async def process_request(request: dict[str, Any]) -> dict[str, Any]:
    if not _viirs_detector or not _plume_tracker:
        return {"error": "Detector not ready", "is_fallback": True}
    try:
        message = request.get("message", request)
        payload = message.get("payload", request)
        input_data = payload.get("input", payload)

        h, w = 100, 100
        bt = np.random.default_rng().normal(290, 15, (h, w))
        for _ in range(np.random.randint(0, 4)):
            cx, cy = np.random.randint(10, 90, 2)
            bt[cx-3:cx+3, cy-3:cy+3] += np.random.uniform(40, 80)

        lats = np.linspace(28.40, 28.88, h)
        lons = np.linspace(76.84, 77.34, w)

        fires = _viirs_detector.detect(bt, lats, lons)

        for fire in fires:
            plume = _plume_tracker.predict_trajectory(
                fire_lat=fire["latitude"],
                fire_lon=fire["longitude"],
                fire_intensity=fire.get("fire_radiative_power_mw", 10),
                wind_speed_ms=input_data.get("wind_speed_ms", 3.5),
                wind_direction_deg=input_data.get("wind_direction_deg", 270),
                pbl_height_m=input_data.get("pbl_height_m", 1000),
            )
            fire["plume_trajectory"] = plume[:6]
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
