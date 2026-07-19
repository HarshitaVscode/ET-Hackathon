"""
Vayu-Drishti Ingestion Service — Entry Point.

Orchestrates all data connectors, manages their lifecycle,
and exposes a health check endpoint for Kubernetes probes.
"""

from __future__ import annotations

import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.config import config
from src.connectors import (
    CAAQMSConnector,
    CitizenConnector,
    SatelliteConnector,
    TrafficConnector,
    WeatherConnector,
)
from src.schemas.models import CitizenReport
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Global connector registry
_connectors: dict[str, Any] = {}


class SubmitReportRequest(BaseModel):
    """Request schema for citizen report submission."""
    latitude: float
    longitude: float
    report_type: str
    description: str | None = None
    image_urls: list[str] = []
    severity_rating: int | None = None
    citizen_id: str | None = None
    ward: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize and start all connectors."""
    setup_logging()
    logger.info("Starting Vayu-Drishti Ingestion Service")

    connectors = {
        "caaqms": CAAQMSConnector(),
        "satellite": SatelliteConnector(),
        "weather": WeatherConnector(),
        "traffic": TrafficConnector(),
        "citizen": CitizenConnector(),
    }

    for name, conn in connectors.items():
        try:
            await conn.initialize()
            _connectors[name] = conn
            logger.info("Connector initialized", name=name)
        except Exception:
            logger.exception("Connector failed to initialize", name=name)

    # Start polling for all connectors except citizen (which is push-based)
    polling_intervals = {
        "caaqms": config.cpcb_poll_interval_seconds,
        "satellite": 3600,
        "weather": config.imd_poll_interval_hours * 3600,
        "traffic": config.google_traffic_poll_interval_seconds,
    }

    for name, interval in polling_intervals.items():
        conn = _connectors.get(name)
        if conn:
            await conn.start_polling(interval_seconds=interval)

    yield

    # Shutdown
    logger.info("Shutting down Vayu-Drishti Ingestion Service")
    for conn in _connectors.values():
        await conn.stop()
    _connectors.clear()


app = FastAPI(
    title="Vayu-Drishti Ingestion API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Kubernetes liveness/readiness probe."""
    statuses = {name: conn.status.value for name, conn in _connectors.items()}
    all_running = all(s == "running" for s in statuses.values() if s != "initialized")
    return {
        "status": "healthy" if all_running else "degraded",
        "service": config.app_name,
        "connectors": statuses,
    }


@app.post("/api/v1/reports")
async def submit_report(request: SubmitReportRequest) -> dict[str, Any]:
    """Submit a citizen pollution report."""
    citizen_conn = _connectors.get("citizen")
    if not citizen_conn:
        raise HTTPException(status_code=503, detail="Citizen connector not available")

    report = CitizenReport(
        report_id="",
        latitude=request.latitude,
        longitude=request.longitude,
        city="Delhi",
        report_type=request.report_type,
        description=request.description,
        image_urls=request.image_urls,
        severity_rating=request.severity_rating,
        citizen_id=request.citizen_id,
        ward=request.ward,
    )

    report_id = await citizen_conn.submit_report(report)
    return {"status": "queued", "report_id": report_id, "message": "Report submitted for verification"}


@app.get("/api/v1/stats")
async def ingestion_stats() -> dict[str, Any]:
    """Get ingestion pipeline statistics."""
    return {
        "connectors": list(_connectors.keys()),
        "statuses": {name: conn.status.value for name, conn in _connectors.items()},
    }


def main() -> None:
    """Entry point for running the ingestion service directly."""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8100,
        reload=config.app_debug,
        log_level=config.app_log_level.lower(),
    )


if __name__ == "__main__":
    main()
