"""
VIIRS thermal anomaly detector for active fire detection.

Processes VIIRS (Visible Infrared Imaging Radiometer Suite) 375m
thermal anomaly data to detect active fires and agricultural burning.

Reference: Schroeder et al., "The VIIRS 375m active fire detection
and characterization algorithm", 2014.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from src.config import burn_config


class VIIRSFireDetector:
    """Detect active fires from VIIRS thermal anomaly data.

    Identifies fire pixels based on brightness temperature thresholds
    and contextual analysis of the 375m I-band data.
    """

    def __init__(self) -> None:
        self.confidence_threshold = burn_config.viirs_fire_confidence_threshold
        self.min_areas_hectares = burn_config.min_burn_area_hectares

    def detect(
        self,
        brightness_temperatures: np.ndarray,
        latitudes: np.ndarray,
        longitudes: np.ndarray,
        timestamps: list[datetime] | None = None,
    ) -> list[dict[str, Any]]:
        """Detect active fire pixels from VIIRS thermal data.

        Args:
            brightness_temperatures: [H, W] array of BT in Kelvin (I-4 band, 3.74µm)
            latitudes: [H] latitude array
            longitudes: [W] longitude array
            timestamps: Per-pixel timestamps (optional)

        Returns:
            List of detected fire events with location and intensity.
        """
        fires: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Threshold-based detection (contextual algorithm simplified)
        # Typical fire pixels have BT > 330K for 3.74µm
        fire_mask = brightness_temperatures > 330.0

        # Cluster adjacent fire pixels
        from scipy.ndimage import label

        labeled_array, num_features = label(fire_mask)

        for feature_id in range(1, num_features + 1):
            mask = labeled_array == feature_id
            fire_pixels = np.sum(mask)
            if fire_pixels < 2:  # Minimum cluster size
                continue

            # Fire location (centroid)
            y_indices, x_indices = np.where(mask)
            center_y = np.mean(y_indices).astype(int)
            center_x = np.mean(x_indices).astype(int)

            # Area estimate (375m resolution → 0.14 ha per pixel)
            area_ha = fire_pixels * 0.140625

            if area_ha < self.min_areas_hectares:
                continue

            # Fire intensity metrics
            bt_values = brightness_temperatures[mask]
            max_bt = float(np.max(bt_values))
            mean_bt = float(np.mean(bt_values))

            lat = float(latitudes[center_y]) if center_y < len(latitudes) else 0
            lon = float(longitudes[center_x]) if center_x < len(longitudes) else 0

            # Confidence based on BT anomaly strength
            fire_confidence = min(1.0, (mean_bt - 300) / 100)

            if fire_confidence < self.confidence_threshold:
                continue

            # Fire radiative power estimate (simplified)
            frp = 4.34e-19 * (max_bt ** 8 - 300 ** 8) * 0.14  # MW per pixel

            fires.append({
                "detection_source": "VIIRS",
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "area_hectares": round(area_ha, 2),
                "fire_pixels": int(fire_pixels),
                "max_brightness_temperature_k": round(max_bt, 1),
                "mean_brightness_temperature_k": round(mean_bt, 1),
                "fire_radiative_power_mw": round(frp, 2),
                "confidence": round(fire_confidence, 3),
                "detected_at": now.isoformat(),
            })

        return fires
