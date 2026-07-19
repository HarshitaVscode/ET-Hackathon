"""
Citizen report ingestion connector.

Receives pollution reports from the mobile app, WhatsApp bot,
and web portal via REST API. Validates and enriches reports
before producing to Kafka.

This connector acts as both a REST endpoint (receiving from apps)
and a poller (for social media and SMS gateways).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.config import config
from src.connectors.base import BaseConnector
from src.schemas.models import CitizenReport
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CitizenConnector(BaseConnector):
    """Connector for ingesting citizen pollution reports."""

    def __init__(self) -> None:
        super().__init__("citizen")
        self._pending_reports: asyncio.Queue[CitizenReport] = asyncio.Queue(maxsize=10000)

    def _validate_config(self) -> None:
        pass  # REST API is always available

    async def _connect_source(self) -> None:
        logger.info("Citizen connector ready — accepting reports via submit_report()")

    async def _disconnect_source(self) -> None:
        self._pending_reports = asyncio.Queue()

    async def submit_report(self, report: CitizenReport) -> str:
        """Submit a citizen report (called by REST API handler)."""
        if not report.report_id:
            report.report_id = f"CR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6]}"
        report.timestamp = report.timestamp or datetime.now(timezone.utc)
        await self._pending_reports.put(report)
        logger.info("Citizen report queued", report_id=report.report_id)
        return report.report_id

    async def _fetch_batch(self) -> list[CitizenReport]:
        """Drain the pending reports queue."""
        batch: list[CitizenReport] = []
        while not self._pending_reports.empty() and len(batch) < 100:
            try:
                report = self._pending_reports.get_nowait()
                batch.append(report)
            except asyncio.QueueEmpty:
                break

        if batch:
            logger.info("Dequeued citizen reports", count=len(batch))
        return batch

    def _serialize_message(self, message: CitizenReport) -> bytes:
        return message.model_dump_json().encode("utf-8")

    def _get_topic(self) -> str:
        return config.kafka_citizen_topic

    def _get_message_key(self, message: CitizenReport) -> str:
        return message.report_id

    async def validate_and_enrich(self, raw: dict[str, Any]) -> CitizenReport | None:
        """Validate and enrich a raw citizen report submission."""
        try:
            report = CitizenReport(**raw)
            _apply_defaults(report)
            return report
        except Exception as exc:
            logger.warning("Invalid citizen report", error=str(exc))
            return None


def _apply_defaults(report: CitizenReport) -> None:
    """Apply sensible defaults to a citizen report."""
    if not report.report_id:
        report.report_id = f"CR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6]}"
    if not report.timestamp:
        report.timestamp = datetime.now(timezone.utc)
