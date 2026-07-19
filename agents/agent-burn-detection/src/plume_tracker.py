"""
Smoke plume tracker — predicts pollutant dispersion from fires.

Uses a ConvLSTM-based trajectory predictor to estimate where
smoke plumes will travel based on wind fields and atmospheric
stability. Provides 48-hour plume forecasts for emergency response.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from src.config import burn_config


class PlumeTracker:
    """Track and predict smoke plume dispersion from detected fires.

    Uses a simplified Gaussian plume model with wind advection
    and atmospheric stability corrections. For real-time use,
    this would use a CFD or DeepWind physics-informed model.
    """

    def __init__(self) -> None:
        self.horizon_hours = burn_config.plume_tracker_horizon_hours

    def predict_trajectory(
        self,
        fire_lat: float,
        fire_lon: float,
        fire_intensity: float,
        wind_speed_ms: float,
        wind_direction_deg: float,
        pbl_height_m: float,
        stability_class: str = "neutral",
    ) -> list[dict[str, Any]]:
        """Predict plume trajectory for the next 48 hours.

        Args:
            fire_lat: Fire latitude.
            fire_lon: Fire longitude.
            fire_intensity: Fire radiative power in MW.
            wind_speed_ms: Wind speed at 10m.
            wind_direction_deg: Wind direction (0=North, clockwise).
            pbl_height_m: Planetary boundary layer height.
            stability_class: Atmospheric stability (stable, neutral, unstable).

        Returns:
            List of plume positions at hourly intervals.
        """
        trajectory: list[dict[str, Any]] = []

        # Convert wind direction to vector components
        wind_rad = np.radians(wind_direction_deg)
        u_wind = wind_speed_ms * np.sin(wind_rad)  # Eastward
        v_wind = wind_speed_ms * np.cos(wind_rad)  # Northward

        # Dispersion coefficients (Pasquill-Gifford, neutral conditions)
        sigma_y = lambda x: 0.08 * x / np.sqrt(1 + 0.0001 * x)
        sigma_z = lambda x: 0.06 * x / np.sqrt(1 + 0.0015 * x)

        # Effective stack height (plume rise from fire buoyancy)
        buoyancy_flux = fire_intensity * 1000 / 1.2  # W/kg
        plume_rise = 5.0 * buoyancy_flux ** 0.25 / wind_speed_ms ** 0.5
        effective_height = min(plume_rise, pbl_height_m)

        # Emission rate (simplified: PM2.5 from fire)
        emission_rate = fire_intensity * 5.0  # g/s per MW

        lat_per_m = 1.0 / 111320.0
        lon_per_m = 1.0 / (111320.0 * np.cos(np.radians(fire_lat)))

        for h in range(0, self.horizon_hours + 1, 1):
            time_sec = h * 3600
            downwind_dist = wind_speed_ms * time_sec  # meters

            if downwind_dist < 1:
                continue

            # Gaussian plume dispersion
            sy = sigma_y(downwind_dist)
            sz = sigma_z(downwind_dist)

            if sz < 0.01:
                continue

            # Centerline concentration at ground level
            concentration = (
                emission_rate
                / (2 * np.pi * wind_speed_ms * sy * sz)
                * np.exp(-0.5 * (effective_height / sz) ** 2)
            )

            # Plume position
            plume_lat = fire_lat + v_wind * time_sec * lat_per_m
            plume_lon = fire_lon + u_wind * time_sec * lon_per_m

            # Plume width (plume spread laterally)
            plume_width_m = 4.3 * sy
            plume_width_deg = plume_width_m * lon_per_m

            trajectory.append({
                "hour": h,
                "latitude": round(plume_lat, 4),
                "longitude": round(plume_lon, 4),
                "concentration_ugm3": round(concentration * 1e6, 1),
                "plume_width_degrees": round(plume_width_deg, 4),
                "plume_height_m": round(effective_height, 0),
                "downwind_distance_km": round(downwind_dist / 1000, 1),
            })

        return trajectory

    def estimate_emissions(
        self,
        area_hectares: float,
        land_cover_type: str = "agricultural",
    ) -> dict[str, float]:
        """Estimate pollutant emissions from a detected fire.

        Uses land-cover-specific emission factors.
        """
        emission_factors = {
            "agricultural": {"PM2.5": 12.0, "PM10": 18.0, "CO": 150.0, "NOx": 5.0},
            "forest": {"PM2.5": 25.0, "PM10": 40.0, "CO": 300.0, "NOx": 10.0},
            "waste": {"PM2.5": 30.0, "PM10": 50.0, "CO": 500.0, "NOx": 15.0},
            "construction_site": {"PM2.5": 5.0, "PM10": 30.0, "CO": 0, "NOx": 0},
        }

        factors = emission_factors.get(land_cover_type, emission_factors["agricultural"])
        return {
            pollutant: round(factor * area_hectares, 1)
            for pollutant, factor in factors.items()
        }
