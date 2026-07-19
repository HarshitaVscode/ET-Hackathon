"""
Satellite imagery connector for ISRO, NASA, and ESA missions.

Fetches scenes from:
  - ISRO OCM-3 (Resourcesat-2A) via Bhuvan API
  - ESA Sentinel-2/5P via Copernicus STAC API
  - NASA MODIS/VIIRS via NASA STAC API
  - Landsat 8/9 via USGS STAC API

Produces SatelliteScene messages to Kafka with S3/MinIO references
to the cloud-optimized GeoTIFF assets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from src.config import config
from src.connectors.base import BaseConnector
from src.schemas.models import SatellitePlatform, SatelliteScene
from src.utils.logging import get_logger
from src.utils.retry import CircuitBreaker

logger = get_logger(__name__)


class SatelliteConnector(BaseConnector):
    """Multi-source satellite imagery connector."""

    def __init__(self) -> None:
        super().__init__("satellite")
        self._stac_clients: dict[str, httpx.AsyncClient] = {}
        self._bhuvan_client: httpx.AsyncClient | None = None
        self._circuit_breaker = CircuitBreaker(
            name="satellite-api",
            failure_threshold=3,
            recovery_timeout_seconds=60.0,
        )
        self._last_acquisition: dict[str, datetime] = {}
        self._source_configs: list[dict[str, Any]] = []

    def _validate_config(self) -> None:
        if not config.sentinel_client_id:
            logger.warning("SENTINEL_CLIENT_ID not set — Sentinel data unavailable")

    def _build_source_configs(self) -> list[dict[str, Any]]:
        """Build list of satellite sources to poll."""
        return [
            {
                "name": "sentinel2",
                "platform": SatellitePlatform.SENTINEL_2,
                "base_url": "https://catalogue.dataspace.copernicus.eu/stac",
                "collection": config.sentinel_collection,
                "bbox": [config.city_lon_min, config.city_lat_min, config.city_lon_max, config.city_lat_max],
                "max_cloud": 30.0,
                "days_back": 5,
                "enabled": bool(config.sentinel_client_id),
            },
            {
                "name": "sentinel5p",
                "platform": SatellitePlatform.SENTINEL_5P,
                "base_url": "https://catalogue.dataspace.copernicus.eu/stac",
                "collection": "sentinel-5p-l2",
                "bbox": [config.city_lon_min, config.city_lat_min, config.city_lon_max, config.city_lat_max],
                "max_cloud": 80.0,
                "days_back": 1,
                "enabled": bool(config.sentinel_client_id),
            },
            {
                "name": "modis",
                "platform": SatellitePlatform.MODIS_TERRA,
                "base_url": "https://cmr.earthdata.nasa.gov/stac",
                "collection": "MODIS-Terra-L2-AOD",
                "bbox": [config.city_lon_min, config.city_lat_min, config.city_lon_max, config.city_lat_max],
                "max_cloud": 40.0,
                "days_back": 1,
                "enabled": True,
            },
            {
                "name": "viirs",
                "platform": SatellitePlatform.VIIRS,
                "base_url": "https://cmr.earthdata.nasa.gov/stac",
                "collection": "VIIRS-SNPP-L2-Fire",
                "bbox": [config.city_lon_min, config.city_lat_min, config.city_lon_max, config.city_lat_max],
                "max_cloud": 90.0,
                "days_back": 1,
                "enabled": True,
            },
        ]

    async def _connect_source(self) -> None:
        self._source_configs = self._build_source_configs()
        for src in self._source_configs:
            if not src["enabled"]:
                continue
            client = httpx.AsyncClient(
                base_url=src["base_url"].rstrip("/"),
                timeout=httpx.Timeout(60.0, connect=15.0),
            )
            self._stac_clients[src["name"]] = client
            self._last_acquisition[src["name"]] = datetime.now(timezone.utc) - timedelta(days=src["days_back"])

        if config.bhuvan_api_key:
            self._bhuvan_client = httpx.AsyncClient(
                base_url=config.bhuvan_api_base.rstrip("/"),
                params={"api_key": config.bhuvan_api_key},
                timeout=httpx.Timeout(60.0, connect=15.0),
            )

    async def _disconnect_source(self) -> None:
        for client in self._stac_clients.values():
            await client.aclose()
        self._stac_clients.clear()
        if self._bhuvan_client:
            await self._bhuvan_client.aclose()
            self._bhuvan_client = None

    async def _fetch_batch(self) -> list[SatelliteScene]:
        """Fetch new satellite scenes from all configured sources."""
        scenes: list[SatelliteScene] = []
        now = datetime.now(timezone.utc)

        for src in self._source_configs:
            if not src["enabled"]:
                continue
            try:
                new_scenes = await self._circuit_breaker.call(
                    self._fetch_source_scenes,
                    src,
                )
                scenes.extend(new_scenes)
                if new_scenes:
                    self._last_acquisition[src["name"]] = now
            except Exception:
                logger.warning("Satellite source failed", source=src["name"])

        logger.info("Fetched satellite scenes", count=len(scenes))
        return scenes

    async def _fetch_source_scenes(self, source: dict[str, Any]) -> list[SatelliteScene]:
        """Query STAC API for new scenes from a specific source."""
        now = datetime.now(timezone.utc)
        client = self._stac_clients.get(source["name"])
        if not client:
            return []

        start_date = self._last_acquisition.get(source["name"], now - timedelta(days=5))
        response = await client.get(
            "/search",
            params={
                "collections": source["collection"],
                "bbox": ",".join(str(b) for b in source["bbox"]),
                "datetime": f"{start_date.isoformat()}/now",
                "limit": 50,
                "sortby": "-properties.datetime",
            },
        )
        response.raise_for_status()
        data = response.json()

        scenes: list[SatelliteScene] = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            cloud = float(props.get("cloud_cover", props.get("eo:cloud_cover", 0)))
            if cloud > source["max_cloud"]:
                continue

            bbox = feature.get("bbox", [0, 0, 0, 0])
            assets = feature.get("assets", {})
            bands = [k for k, v in assets.items() if v.get("type", "").startswith("image/")]
            data_url = next(
                (v["href"] for v in assets.values() if v.get("type", "").startswith("image/")),
                "",
            )
            scene_id = feature.get("id", f"{source['name']}_{now.strftime('%Y%m%d_%H%M%S')}")

            scenes.append(SatelliteScene(
                scene_id=scene_id,
                platform=source["platform"],
                acquisition_time=datetime.fromisoformat(props.get("datetime", now.isoformat())),
                bounding_box=tuple(bbox),
                cloud_cover_percent=cloud,
                bands_available=bands,
                data_url=data_url,
                file_format="GeoTIFF",
                size_mb=None,
                raw_metadata=feature,
            ))
        return scenes

    def _serialize_message(self, message: SatelliteScene) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return config.kafka_satellite_topic

    def _get_message_key(self, message: SatelliteScene) -> str:
        return f"{message.platform.value}:{message.scene_id}"
