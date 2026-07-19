from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class VIIRSFireDetector:
    def __init__(self, bt_threshold: float = 330.0, min_pixels: int = 3):
        self.bt_threshold = bt_threshold
        self.min_pixels = min_pixels

    def detect(self, brightness_temperature: np.ndarray, lats: np.ndarray, lons: np.ndarray) -> list[dict[str, Any]]:
        hotspots = brightness_temperature > self.bt_threshold
        labeled, num_features = ndimage.label(hotspots)

        fires = []
        for i in range(1, num_features + 1):
            mask = labeled == i
            pixel_count = int(np.sum(mask))
            if pixel_count < self.min_pixels:
                continue

            ys, xs = np.where(mask)
            area_km2 = pixel_count * 0.375 * 0.375

            if lats.ndim == 1 and lons.ndim == 1:
                fire_lat = float(np.mean(lats[ys]))
                fire_lon = float(np.mean(lons[xs]))
            else:
                fire_lat = float(np.mean(lats[ys, xs]))
                fire_lon = float(np.mean(lons[ys, xs]))

            max_bt = float(np.max(brightness_temperature[mask]))
            mean_bt = float(np.mean(brightness_temperature[mask]))
            frp = 0.5 * area_km2 * (mean_bt - 300) / 10

            fires.append({
                "latitude": fire_lat,
                "longitude": fire_lon,
                "max_brightness_temperature_k": round(max_bt, 1),
                "mean_brightness_temperature_k": round(mean_bt, 1),
                "area_hectares": round(area_km2 * 100, 2),
                "area_km2": round(area_km2, 4),
                "fire_radiative_power_mw": round(frp, 2),
                "pixel_count": pixel_count,
                "detection_source": "VIIRS",
                "confidence": min(1.0, pixel_count / 20),
            })

        logger.info(f"Fire detection complete: {len(fires)} fires found")
        return fires
