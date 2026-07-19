from __future__ import annotations

from typing import Any

import numpy as np

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class PlumeTracker:
    def __init__(self) -> None:
        self.pasquill_classes = {
            "a": (0.22, 0.20, 0.50, 0.50),
            "b": (0.16, 0.12, 0.50, 0.50),
            "c": (0.11, 0.08, 0.20, 0.20),
            "d": (0.08, 0.06, 0.06, 0.06),
            "e": (0.06, 0.03, 0.03, 0.03),
            "f": (0.04, 0.02, 0.02, 0.02),
        }

    def predict_trajectory(
        self,
        fire_lat: float,
        fire_lon: float,
        fire_intensity: float,
        wind_speed_ms: float,
        wind_direction_deg: float,
        pbl_height_m: float,
        stability_class: str = "neutral",
        hours: int = 48,
    ) -> list[dict[str, Any]]:
        stability_map = {"very_unstable": "a", "unstable": "b", "slightly_unstable": "c",
                         "neutral": "d", "stable": "e", "very_stable": "f"}
        pg = stability_map.get(stability_class.lower(), "d")
        params = self.pasquill_classes.get(pg, self.pasquill_classes["d"])

        wind_rad = np.radians(wind_direction_deg)
        u = -wind_speed_ms * np.sin(wind_rad)
        v = -wind_speed_ms * np.cos(wind_rad)

        emission_rate = fire_intensity * 100
        trajectory = []

        for hour in range(hours + 1):
            t = hour * 3600
            downwind = wind_speed_ms * t
            sigma_y = params[0] * downwind / (1 + params[1] * downwind / 1000) ** 0.5
            sigma_z = params[2] * downwind / (1 + params[3] * downwind / 1000) ** 0.5

            lat_delta = v * t / 111000
            lon_delta = u * t / (111000 * np.cos(np.radians(fire_lat + lat_delta / 2)))
            plume_lat = fire_lat + lat_delta
            plume_lon = fire_lon + lon_delta

            concentration = emission_rate / (2 * np.pi * sigma_y * sigma_z * wind_speed_ms + 1) if wind_speed_ms > 0 else 0

            trajectory.append({
                "hour": hour,
                "latitude": round(plume_lat, 4),
                "longitude": round(plume_lon, 4),
                "downwind_distance_km": round(downwind / 1000, 1),
                "dispersion_sigma_y_m": round(sigma_y, 1),
                "dispersion_sigma_z_m": round(sigma_z, 1),
                "pm25_concentration_ugm3": round(concentration, 1),
            })

        return trajectory

    def estimate_emissions(
        self,
        area_hectares: float,
        land_cover_type: str = "agricultural",
    ) -> dict[str, float]:
        emission_factors = {
            "agricultural": {"pm25": 15.0, "pm10": 30.0, "co": 120.0, "nox": 5.0},
            "forest": {"pm25": 20.0, "pm10": 40.0, "co": 150.0, "nox": 8.0},
            "waste": {"pm25": 25.0, "pm10": 50.0, "co": 200.0, "nox": 12.0},
            "industrial": {"pm25": 10.0, "pm10": 20.0, "co": 80.0, "nox": 15.0},
        }
        factors = emission_factors.get(land_cover_type, emission_factors["agricultural"])
        return {
            "pm25_tons": round(factors["pm25"] * area_hectares / 100, 2),
            "pm10_tons": round(factors["pm10"] * area_hectares / 100, 2),
            "co_tons": round(factors["co"] * area_hectares / 100, 2),
            "nox_tons": round(factors["nox"] * area_hectares / 100, 2),
        }
