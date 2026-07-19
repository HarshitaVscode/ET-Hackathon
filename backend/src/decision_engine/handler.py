from __future__ import annotations

from typing import Any

from src.decision_engine.optimizer import (
    EmergencyResponseOptimizer,
    SquadRouter,
    TrafficRLOptimizer,
)
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)

_traffic_opt: TrafficRLOptimizer | None = None
_squad_router: SquadRouter | None = None
_emergency: EmergencyResponseOptimizer | None = None


def initialize():
    global _traffic_opt, _squad_router, _emergency
    _traffic_opt = TrafficRLOptimizer()
    _squad_router = SquadRouter()
    _emergency = EmergencyResponseOptimizer()


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


async def optimize_enforcement_route(request: dict[str, Any]) -> dict[str, Any]:
    if not _squad_router:
        return {"error": "Router not ready"}
    plan = _squad_router.optimize_route(
        violations=request.get("violations", []),
        num_squads=request.get("num_squads", 3),
    )
    return {"deployment_plan": plan}


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
