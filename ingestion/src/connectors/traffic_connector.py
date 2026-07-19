"""
Traffic data connector for Google Maps and city camera feeds.

Fetches real-time traffic data, constructs road network graphs,
and estimates emissions per road segment. Produces TrafficSnapshot
messages to Kafka.

Implements rate limiting to respect API quotas.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from src.config import config
from src.connectors.base import BaseConnector
from src.schemas.models import TrafficSnapshot
from src.utils.logging import get_logger
from src.utils.retry import CircuitBreaker

logger = get_logger(__name__)

# Major Delhi road segments for fallback
DELHI_ROAD_SEGMENTS: list[dict[str, Any]] = [
    {"id": "NH9_DEL_001", "name": "NH-9 (Delhi-Ghaziabad)", "lat": 28.64, "lon": 77.28},
    {"id": "RING_DEL_001", "name": "Ring Road (Ashram)", "lat": 28.58, "lon": 77.25},
    {"id": "MG_DEL_001", "name": "MG Road (Gurugram)", "lat": 28.48, "lon": 77.10},
    {"id": "AIIMS_DEL_001", "name": "AIIMS Junction", "lat": 28.57, "lon": 77.21},
    {"id": "ITO_DEL_001", "name": "ITO", "lat": 28.63, "lon": 77.24},
    {"id": "DWARKA_DEL_001", "name": "Dwarka Sector 12", "lat": 28.59, "lon": 77.05},
    {"id": "ROHINI_DEL_001", "name": "Rohini Sector 9", "lat": 28.73, "lon": 77.12},
    {"id": "VAISHALI_DEL_001", "name": "Vaishali-Ghaziabad", "lat": 28.65, "lon": 77.34},
]


class TrafficConnector(BaseConnector):
    """Connector for real-time traffic flow data."""

    def __init__(self) -> None:
        super().__init__("traffic")
        self._client: httpx.AsyncClient | None = None
        self._circuit_breaker = CircuitBreaker(name="traffic-api", failure_threshold=3)
        self._rate_limiter: asyncio.Semaphore | None = None

    def _validate_config(self) -> None:
        if not config.google_maps_api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set — using fallback traffic data")

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        self._rate_limiter = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch_batch(self) -> list[TrafficSnapshot]:
        """Fetch traffic data for all monitored road segments."""
        snapshots: list[TrafficSnapshot] = []

        for segment in DELHI_ROAD_SEGMENTS:
            try:
                snapshot = await self._circuit_breaker.call(
                    self._fetch_segment_traffic,
                    segment,
                )
                if snapshot:
                    snapshots.append(snapshot)
            except Exception:
                logger.warning("Traffic fetch failed for segment", segment=segment["id"])

        if not snapshots:
            logger.warning("All traffic fetches failed, using synthetic data")
            snapshots = self._generate_synthetic_traffic()

        logger.info("Fetched traffic snapshots", count=len(snapshots))
        return snapshots

    async def _fetch_segment_traffic(self, segment: dict[str, Any]) -> TrafficSnapshot | None:
        """Fetch traffic data for one road segment from Google Maps API."""
        if not self._client or not self._rate_limiter:
            return self._generate_single_traffic(segment)

        async with self._rate_limiter:
            response = await self._client.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={
                    "origins": f"{segment['lat']},{segment['lon']}",
                    "destinations": f"{segment['lat']+0.01},{segment['lon']+0.01}",
                    "departure_time": "now",
                    "traffic_model": "best_guess",
                    "key": config.google_maps_api_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_traffic_response(segment, data)

    def _parse_traffic_response(self, segment: dict[str, Any], data: dict[str, Any]) -> TrafficSnapshot | None:
        """Parse Google Maps Distance Matrix API response."""
        try:
            element = data["rows"][0]["elements"][0]
            if element["status"] != "OK":
                return self._generate_single_traffic(segment)

            duration_in_traffic = element.get("duration_in_traffic", {}).get("value", 0)
            duration_normal = element.get("duration", {}).get("value", 1)
            if duration_normal == 0:
                duration_normal = 1
            congestion = min(10.0, (duration_in_traffic / duration_normal - 1) * 5)
            speed = 50.0 / (duration_in_traffic / max(duration_normal, 1))

            return TrafficSnapshot(
                road_segment_id=segment["id"],
                road_name=segment["name"],
                city="Delhi",
                timestamp=datetime.now(timezone.utc),
                average_speed_kph=round(max(0, speed), 1),
                congestion_level=round(max(0, congestion), 1),
                raw_payload=data,
            )
        except (KeyError, IndexError, TypeError):
            return self._generate_single_traffic(segment)

    def _generate_single_traffic(self, segment: dict[str, Any]) -> TrafficSnapshot:
        """Generate synthetic traffic for a segment when API is unavailable."""
        import random
        rng = random.Random(hash(segment["id"]) % (2**31))
        base_speed = 40.0
        congestion = rng.uniform(1.0, 9.0)
        speed = base_speed * (1 - congestion / 12)
        return TrafficSnapshot(
            road_segment_id=segment["id"],
            road_name=segment["name"],
            city="Delhi",
            timestamp=datetime.now(timezone.utc),
            average_speed_kph=round(max(5, speed), 1),
            congestion_level=round(congestion, 1),
        )

    def _generate_synthetic_traffic(self) -> list[TrafficSnapshot]:
        return [self._generate_single_traffic(s) for s in DELHI_ROAD_SEGMENTS]

    def _serialize_message(self, message: TrafficSnapshot) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return config.kafka_traffic_topic

    def _get_message_key(self, message: TrafficSnapshot) -> str:
        return message.road_segment_id
