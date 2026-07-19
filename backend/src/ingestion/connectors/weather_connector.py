from __future__ import annotations

from datetime import datetime, timezone

import httpx
import numpy as np

from src.ingestion.connectors.base import BaseConnector
from src.ingestion.schemas.models import WeatherObservation
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class WeatherConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("weather")
        self._client: httpx.AsyncClient | None = None

    def _validate_config(self) -> None:
        pass

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch_batch(self) -> list[WeatherObservation]:
        return self._generate_synthetic_weather()

    def _generate_synthetic_weather(self) -> list[WeatherObservation]:
        rng = np.random.default_rng()
        observations = []
        now = datetime.now(timezone.utc)
        for i in range(6):
            lat = 28.40 + i * 0.08
            for j in range(6):
                lon = 76.84 + j * 0.10
                observations.append(WeatherObservation(
                    source="ERA5",
                    timestamp=now,
                    latitude=round(lat, 4),
                    longitude=round(lon, 4),
                    temperature_celsius=round(30 + 5 * np.sin(np.pi * (now.hour - 12) / 12), 1),
                    relative_humidity_percent=round(55 - 15 * np.sin(np.pi * (now.hour - 12) / 12), 1),
                    wind_speed_ms=round(float(rng.uniform(1, 6)), 1),
                    wind_direction_degrees=int(rng.integers(0, 359)),
                    boundary_layer_height_m=round(float(rng.uniform(500, 1800))),
                ))
        return observations

    def _serialize_message(self, message: WeatherObservation) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return "raw.weather"

    def _get_message_key(self, message: WeatherObservation) -> str:
        return f"{message.latitude}:{message.longitude}"
