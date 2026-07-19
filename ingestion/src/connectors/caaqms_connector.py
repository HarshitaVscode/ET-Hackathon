"""
CPCB CAAQMS (Continuous Ambient Air Quality Monitoring Station) connector.

Polls the CPCB real-time API for air quality measurements from over 400
reference-grade stations across India. Produces SensorReading messages to Kafka.

Uses the Template Method pattern via BaseConnector.
Implements circuit breaker and exponential backoff for resilience.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx

from src.config import config
from src.connectors.base import BaseConnector
from src.schemas.models import PollutantType, SensorQuality, SensorReading
from src.utils.logging import get_logger
from src.utils.retry import CircuitBreaker, with_retry

logger = get_logger(__name__)


# CPCB pollutant name → internal enum mapping
CPCB_POLLUTANT_MAP: dict[str, PollutantType] = {
    "PM2.5": PollutantType.PM2_5,
    "PM10": PollutantType.PM10,
    "NO2": PollutantType.NO2,
    "SO2": PollutantType.SO2,
    "CO": PollutantType.CO,
    "O3": PollutantType.O3,
    "NH3": PollutantType.NH3,
    "BTX": PollutantType.BTX,
}


class CAAQMSConnector(BaseConnector):
    """Connector to the CPCB CAAQMS real-time API."""

    def __init__(self) -> None:
        super().__init__("caaqms")
        self._client: httpx.AsyncClient | None = None
        self._circuit_breaker = CircuitBreaker(
            name="cpcb-api",
            failure_threshold=5,
            recovery_timeout_seconds=30.0,
        )
        self._monitor_stations: list[dict[str, Any]] = []
        self._last_poll: datetime | None = None

    def _validate_config(self) -> None:
        if not config.cpcb_api_base:
            raise ValueError("CPCB_API_BASE is not configured")
        if not config.cpcb_api_key:
            logger.warning("CPCB_API_KEY not set — some endpoints may be rate-limited")

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=config.cpcb_api_base.rstrip("/"),
            headers={"Authorization": f"Bearer {config.cpcb_api_key}"} if config.cpcb_api_key else {},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        await self._load_station_list()

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _load_station_list(self) -> None:
        """Fetch the list of CAAQMS monitoring stations for this city."""
        try:
            if not self._client:
                return
            response = await self._circuit_breaker.call(
                self._client.get,
                "/stations",
                params={"city": "Delhi", "format": "json"},
            )
            response.raise_for_status()
            data = response.json()
            self._monitor_stations = data.get("stations", data.get("data", []))
            logger.info("Loaded CAAQMS stations", count=len(self._monitor_stations))
        except Exception:
            logger.exception("Failed to load station list, using fallback")
            self._monitor_stations = self._get_fallback_stations()

    async def _fetch_batch(self) -> list[SensorReading]:
        """Fetch latest readings from all CAAQMS stations."""
        if not self._client:
            return []
        readings: list[SensorReading] = []
        now = datetime.now(timezone.utc)

        for station in self._monitor_stations:
            try:
                station_id = station.get("id") or station.get("station_id")
                if not station_id:
                    continue
                reading = await self._circuit_breaker.call(
                    self._fetch_station_reading,
                    station,
                )
                if reading:
                    readings.append(reading)
            except Exception:
                logger.warning("Failed to poll station", station_id=station.get("id"))

        self._last_poll = now
        logger.info("Fetched CAAQMS readings", count=len(readings), stations=len(self._monitor_stations))
        return readings

    @with_retry(max_attempts=2)
    async def _fetch_station_reading(self, station: dict[str, Any]) -> SensorReading | None:
        """Fetch a single station's latest reading."""
        if not self._client:
            return None
        station_id = station.get("id") or station.get("station_id")
        response = await self._client.get(
            f"/station/{station_id}/latest",
            params={"format": "json"},
        )
        response.raise_for_status()
        data = response.json()
        return self._parse_station_data(station, data)

    def _parse_station_data(self, station: dict[str, Any], data: dict[str, Any]) -> SensorReading | None:
        """Parse CPCB API response into a SensorReading."""
        pollutants = data.get("pollutants", data.get("data", []))
        if not pollutants:
            return None

        # Get the primary pollutant (highest concentration or first)
        first = pollutants[0] if isinstance(pollutants, list) else pollutants
        pollutant_name = first.get("name") or first.get("pollutant", "")
        concentration = float(first.get("value") or first.get("concentration", 0))
        pollutant_type = CPCB_POLLUTANT_MAP.get(pollutant_name)

        if not pollutant_type:
            logger.debug("Unknown pollutant", name=pollutant_name)
            return None

        return SensorReading(
            sensor_id=f"CPCB-{station.get('id', 'unknown')}",
            station_name=station.get("name") or station.get("station_name"),
            city=station.get("city", "Delhi"),
            ward=station.get("ward"),
            latitude=float(station.get("latitude", station.get("lat", 0))),
            longitude=float(station.get("longitude", station.get("lon", 0))),
            timestamp=datetime.now(timezone.utc),
            pollutant=pollutant_type,
            concentration=concentration,
            sensor_quality=SensorQuality.REFERENCE,
            temperature_celsius=first.get("temperature"),
            humidity_percent=first.get("humidity"),
            wind_speed_ms=first.get("wind_speed"),
            wind_direction_degrees=first.get("wind_direction"),
            raw_payload=data,
        )

    def _serialize_message(self, message: SensorReading) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return config.kafka_sensor_topic

    def _get_message_key(self, message: SensorReading) -> str:
        return f"{message.sensor_id}:{message.pollutant.value}"

    @staticmethod
    def _get_fallback_stations() -> list[dict[str, Any]]:
        """Return hardcoded Delhi stations as fallback when API is unreachable."""
        return [
            {"id": "DL-001", "name": "Delhi - Anand Vihar", "city": "Delhi",
             "latitude": 28.652, "longitude": 77.315},
            {"id": "DL-002", "name": "Delhi - RK Puram", "city": "Delhi",
             "latitude": 28.567, "longitude": 77.183},
            {"id": "DL-003", "name": "Delhi - ITO", "city": "Delhi",
             "latitude": 28.629, "longitude": 77.242},
            {"id": "DL-004", "name": "Delhi - Dwarka", "city": "Delhi",
             "latitude": 28.592, "longitude": 77.046},
            {"id": "DL-005", "name": "Delhi - Narela", "city": "Delhi",
             "latitude": 28.849, "longitude": 77.085},
            {"id": "DL-006", "name": "Delhi - Bawana", "city": "Delhi",
             "latitude": 28.778, "longitude": 77.039},
        ]
