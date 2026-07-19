from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from src.ingestion.connectors.base import BaseConnector
from src.ingestion.schemas.models import SatellitePlatform, SatelliteScene
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class SatelliteConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("satellite")
        self._client: httpx.AsyncClient | None = None

    def _validate_config(self) -> None:
        pass

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch_batch(self) -> list[SatelliteScene]:
        return self._generate_synthetic_scenes()

    def _generate_synthetic_scenes(self) -> list[SatelliteScene]:
        return [
            SatelliteScene(
                scene_id=f"S2A_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_T44RKN",
                platform=SatellitePlatform.SENTINEL_2,
                acquisition_time=datetime.now(timezone.utc),
                bounding_box=(28.40, 28.88, 76.84, 77.34),
                cloud_cover_percent=2.3,
                bands_available=["B01", "B02", "B03", "B04", "B08"],
                data_url=f"/data/satellite/sentinel2/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/scene.tif",
            )
        ]

    def _serialize_message(self, message: SatelliteScene) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return "raw.satellite"

    def _get_message_key(self, message: SatelliteScene) -> str:
        return message.scene_id
