"""REST API routes for the API Gateway."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/aqi/current")
async def get_current_aqi(city: str = "Delhi") -> dict[str, Any]:
    return {
        "city": city,
        "aqi": 285,
        "pm2_5": 128.5,
        "pm10": 245.0,
        "no2": 45.2,
        "timestamp": "2026-07-18T14:30:00Z",
        "source": "CPCB CAAQMS",
        "category": "poor",
    }


@router.get("/aqi/forecast")
async def get_aqi_forecast(city: str = "Delhi", hours: int = 72) -> dict[str, Any]:
    return {
        "city": city,
        "forecasts": [
            {"horizon_hours": h, "mean_aqi": 280 - h * 2, "upper": 310 - h, "lower": 250 - h * 3}
            for h in [1, 3, 6, 12, 24, 48, 72] if h <= hours
        ],
        "model": "graphcast_tft_ensemble",
    }


@router.get("/sources")
async def get_source_attribution(lat: float = 28.61, lon: float = 77.23) -> dict[str, Any]:
    return {
        "location": {"latitude": lat, "longitude": lon},
        "contributions": [
            {"source": "traffic", "percentage": 42.0, "confidence": 0.85},
            {"source": "agricultural_burning", "percentage": 28.0, "confidence": 0.75},
            {"source": "industry", "percentage": 18.0, "confidence": 0.70},
            {"source": "construction", "percentage": 8.0, "confidence": 0.60},
            {"source": "other", "percentage": 4.0, "confidence": 0.50},
        ],
        "causal_model": "causal_dag_pc",
    }


@router.get("/wards/ranking")
async def get_ward_ranking(city: str = "Delhi") -> list[dict[str, Any]]:
    return [
        {"ward_id": "W12", "name": "East Delhi", "aqi": 412, "trend": "rising", "primary_source": "burning"},
        {"ward_id": "W7", "name": "Dwarka", "aqi": 285, "trend": "stable", "primary_source": "construction"},
        {"ward_id": "W4", "name": "Vasant Kunj", "aqi": 210, "trend": "improving", "primary_source": "traffic"},
    ]


@router.get("/enforcement/queue")
async def get_enforcement_queue() -> list[dict[str, Any]]:
    return [
        {"id": 1, "type": "burning", "location": "Ghaziabad border", "priority": "high", "confidence": 0.92},
        {"id": 2, "type": "construction", "location": "Sector 15, Plot 47", "priority": "medium", "confidence": 0.78},
        {"id": 3, "type": "industry", "location": "Wazirpur", "priority": "medium", "confidence": 0.65},
    ]


@router.get("/health/alerts")
async def get_health_alerts() -> list[dict[str, Any]]:
    return [
        {"ward": "East Delhi", "risk": "high", "population_at_risk": 12000, "advisory": "Avoid outdoor activity"},
        {"ward": "Ghaziabad", "risk": "high", "population_at_risk": 8500, "advisory": "Schools closed tomorrow"},
        {"ward": "Dwarka", "risk": "moderate", "population_at_risk": 3000, "advisory": "Sensitive groups limit exertion"},
    ]


@router.post("/policy/simulate")
async def simulate_policy(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy": request.get("policy_name", "unknown"),
        "current_aqi": 285,
        "predicted_aqi": 220,
        "reduction_percent": 22.8,
        "confidence": 0.75,
        "estimated_health_savings_cr": 12.5,
    }
