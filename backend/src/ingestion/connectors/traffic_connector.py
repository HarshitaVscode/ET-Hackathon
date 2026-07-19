from __future__ import annotations

from datetime import datetime, timezone

import httpx
import numpy as np

from src.ingestion.connectors.base import BaseConnector
from src.ingestion.schemas.models import TrafficSnapshot
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class TrafficConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("traffic")
        self._client: httpx.AsyncClient | None = None

    def _validate_config(self) -> None:
        pass

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch_batch(self) -> list[TrafficSnapshot]:
        return self._generate_synthetic_traffic()

    def _generate_synthetic_traffic(self) -> list[TrafficSnapshot]:
        rng = np.random.default_rng()
        now = datetime.now(timezone.utc)
        hour = now.hour
        roads = [
            ("NH9", 28.66, 77.35, "highway"),
            ("Ring_Road", 28.58, 77.25, "arterial"),
            ("MG_Road", 28.48, 77.10, "arterial"),
            ("AIIMS", 28.57, 77.21, "residential"),
        ]
        snapshots = []
        for road_id, lat, lon, road_type in roads:
            congestion = 3 + 5 * np.exp(-((hour - 9) ** 2) / 50) + 4 * np.exp(-((hour - 18) ** 2) / 30) + float(rng.normal(0, 0.5))
            congestion = max(0, min(10, congestion))
            snapshots.append(TrafficSnapshot(
                road_segment_id=road_id,
                road_name=road_id,
                city="Delhi",
                timestamp=now,
                average_speed_kph=round(50 / max(1, congestion), 1),
                congestion_level=round(congestion, 1),
                road_type=road_type,
            ))
        return snapshots

    def _serialize_message(self, message: TrafficSnapshot) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return "raw.traffic"

    def _get_message_key(self, message: TrafficSnapshot) -> str:
        return message.road_segment_id
