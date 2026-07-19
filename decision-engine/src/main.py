"""
Decision Engine — Entry Point.

Optimizes traffic signals, enforcement squad routing,
and emergency response actions. Converts AI predictions
into actionable municipal decisions.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.config import decision_config
from src.optimizer import (
    EmergencyResponseOptimizer,
    SquadRouter,
    TrafficRLOptimizer,
)

logger = __import__("structlog").get_logger(__name__)

_traffic_opt: TrafficRLOptimizer | None = None
_squad_router: SquadRouter | None = None
_emergency: EmergencyResponseOptimizer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _traffic_opt, _squad_router, _emergency
    _traffic_opt = TrafficRLOptimizer()
    _squad_router = SquadRouter()
    _emergency = EmergencyResponseOptimizer()
    yield


app = FastAPI(
    title="Vayu-Drishti Decision Engine",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/v1/traffic/optimize")
async def optimize_traffic(request: dict[str, Any]) -> dict[str, Any]:
    if not _traffic_opt:
        return {"error": "Optimizer not ready"}
    recommendations = _traffic_opt.optimize_timing(
        congestion_levels=request.get("congestion_levels", {}),
        current_aqi=request.get("current_aqi", 200),
        wind_speed_ms=request.get("wind_speed_ms", 3),
        time_hour=request.get("time_hour", 12),
    )
    return {"recommendations": recommendations}


@app.post("/api/v1/enforcement/route")
async def optimize_enforcement_route(request: dict[str, Any]) -> dict[str, Any]:
    if not _squad_router:
        return {"error": "Router not ready"}
    plan = _squad_router.optimize_route(
        violations=request.get("violations", []),
        num_squads=request.get("num_squads", 3),
    )
    return {"deployment_plan": plan}


@app.post("/api/v1/emergency/assess")
async def assess_emergency(request: dict[str, Any]) -> dict[str, Any]:
    if not _emergency:
        return {"error": "Emergency evaluator not ready"}
    assessment = _emergency.evaluate_severity(
        current_aqi=request.get("current_aqi", 200),
        forecast_peak_aqi=request.get("forecast_peak_aqi", 250),
        affected_population=request.get("affected_population", 100000),
        duration_hours=request.get("duration_hours", 24),
        vulnerable_population=request.get("vulnerable_population", 20000),
    )
    return assessment


@app.post("/api/v1/process")
async def process(request: dict[str, Any]) -> dict[str, Any]:
    """Unified processing endpoint called by orchestrator."""
    if not all([_traffic_opt, _squad_router, _emergency]):
        return {"error": "Decision engine not ready", "is_fallback": True}
    return {
        "traffic": await optimize_traffic(request),
        "enforcement": await optimize_enforcement_route(request),
        "emergency": await assess_emergency(request),
    }


def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=decision_config.app_port,
        reload=decision_config.app_debug,
    )


if __name__ == "__main__":
    main()
