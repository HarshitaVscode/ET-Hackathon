from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from src.ingestion.connectors.base import BaseConnector
from src.ingestion.schemas.models import CitizenReport
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class CitizenConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("citizen")
        self._client: httpx.AsyncClient | None = None

    def _validate_config(self) -> None:
        pass

    async def _connect_source(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def _disconnect_source(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _fetch_batch(self) -> list[CitizenReport]:
        return self._generate_synthetic_reports()

    def _generate_synthetic_reports(self) -> list[CitizenReport]:
        return [
            CitizenReport(
                report_id=f"CR-{uuid4().hex[:8].upper()}",
                citizen_id=f"CIT-{uuid4().hex[:4].upper()}",
                city="Delhi",
                latitude=28.62,
                longitude=77.24,
                timestamp=datetime.now(timezone.utc),
                report_type="burning",
                description="Burning smell and visible smoke near sector 12 market",
                severity_rating=4,
                verification_status="pending",
            )
        ]

    def _serialize_message(self, message: CitizenReport) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return "raw.citizen"

    def _get_message_key(self, message: CitizenReport) -> str:
        return message.report_id

    async def submit_report(self, report: CitizenReport) -> str:
        report.report_id = f"CR-{uuid4().hex[:8].upper()}"
        report.timestamp = datetime.now(timezone.utc)
        payload = json.loads(report.model_dump_json())
        await self._event_bus.publish(topic=self._get_topic(), message=payload, key=report.report_id)
        logger.info("Citizen report submitted", report_id=report.report_id)
        return report.report_id
