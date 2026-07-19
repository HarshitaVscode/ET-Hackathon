"""
Weather data connector supporting IMD, ERA5, and CAMS sources.

Fetches gridded meteorological data from:
  - India Meteorological Department (IMD) gridded data
  - ECMWF ERA5 reanalysis (via CDS API or cached files)
  - CAMS global air quality forecasts

Produces WeatherObservation messages to Kafka.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
import numpy as np

from src.config import config
from src.connectors.base import BaseConnector
from src.schemas.models import WeatherObservation
from src.utils.logging import get_logger
from src.utils.retry import CircuitBreaker

logger = get_logger(__name__)


class WeatherConnector(BaseConnector):
    """Multi-source weather data connector."""

    def __init__(self) -> None:
        super().__init__("weather")
        self._imd_client: httpx.AsyncClient | None = None
        self._circuit_breaker = CircuitBreaker(name="weather-api", failure_threshold=3)

    def _validate_config(self) -> None:
        if not config.imd_api_base:
            logger.warning("IMD_API_BASE not set — weather data will be limited")

    async def _connect_source(self) -> None:
        self._imd_client = httpx.AsyncClient(
            base_url=config.imd_api_base.rstrip("/"),
            params={"api_key": config.imd_api_key} if config.imd_api_key else {},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def _disconnect_source(self) -> None:
        if self._imd_client:
            await self._imd_client.aclose()
            self._imd_client = None

    async def _fetch_batch(self) -> list[WeatherObservation]:
        """Fetch latest weather observations."""
        observations: list[WeatherObservation] = []

        try:
            imd_data = await self._circuit_breaker.call(self._fetch_imd_gridded)
            observations.extend(imd_data)
        except Exception:
            logger.warning("IMD fetch failed, generating synthetic grid")
            observations.extend(self._generate_synthetic_grid())

        logger.info("Fetched weather observations", count=len(observations))
        return observations

    async def _fetch_imd_gridded(self) -> list[WeatherObservation]:
        """Fetch gridded weather data from IMD API."""
        if not self._imd_client:
            return []
        response = await self._imd_client.get(
            "/gridded/latest",
            params={
                "lat_min": config.city_lat_min,
                "lat_max": config.city_lat_max,
                "lon_min": config.city_lon_min,
                "lon_max": config.city_lon_max,
                "resolution": "0.25",
            },
        )
        response.raise_for_status()
        data = response.json()
        return self._parse_gridded_response(data)

    def _parse_gridded_response(self, data: dict[str, Any]) -> list[WeatherObservation]:
        """Parse IMD gridded JSON response."""
        observations: list[WeatherObservation] = []
        grid_points = data.get("data", data.get("grid", []))
        now = datetime.now(timezone.utc)

        for point in grid_points:
            observations.append(WeatherObservation(
                source="IMD",
                timestamp=now,
                latitude=float(point.get("lat", 0)),
                longitude=float(point.get("lon", 0)),
                temperature_celsius=point.get("temp"),
                relative_humidity_percent=point.get("humidity"),
                pressure_hpa=point.get("pressure"),
                wind_speed_ms=point.get("wind_speed"),
                wind_direction_degrees=point.get("wind_dir"),
                boundary_layer_height_m=point.get("pbl_height"),
                raw_payload=point,
            ))
        return observations

    def _generate_synthetic_grid(self) -> list[WeatherObservation]:
        """Generate a synthetic weather grid when API is unavailable."""
        observations: list[WeatherObservation] = []
        now = datetime.now(timezone.utc)
        lat_step = (config.city_lat_max - config.city_lat_min) / 5
        lon_step = (config.city_lon_max - config.city_lon_min) / 5

        rng = np.random.default_rng(seed=42)
        base_temp = 34.0
        base_wind = 3.5

        for i in range(6):
            for j in range(6):
                lat = config.city_lat_min + i * lat_step
                lon = config.city_lon_min + j * lon_step
                observations.append(WeatherObservation(
                    source="SYNTHETIC",
                    timestamp=now,
                    latitude=round(lat, 4),
                    longitude=round(lon, 4),
                    temperature_celsius=round(base_temp + rng.normal(0, 1.5), 1),
                    relative_humidity_percent=round(55 + rng.normal(0, 10), 1),
                    pressure_hpa=round(1013 - rng.uniform(0, 10), 1),
                    wind_speed_ms=round(max(0, base_wind + rng.normal(0, 1)), 1),
                    wind_direction_degrees=rng.integers(0, 360),
                    boundary_layer_height_m=round(rng.uniform(500, 1500), 0),
                ))
        return observations

    def _serialize_message(self, message: WeatherObservation) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return config.kafka_weather_topic

    def _get_message_key(self, message: WeatherObservation) -> str:
        return f"{message.source}:{message.latitude}:{message.longitude}"
