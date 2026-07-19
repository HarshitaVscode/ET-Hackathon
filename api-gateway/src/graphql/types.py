"""GraphQL type definitions."""

from __future__ import annotations

from typing import Any

import strawberry


@strawberry.type
class AQIForecast:
    timestamp: str
    mean_aqi: float
    min_aqi: float
    max_aqi: float
    confidence: float
    horizon_hours: int


@strawberry.type
class SourceAttribution:
    source_type: str
    percentage: float
    absolute_contribution: float
    confidence: float


@strawberry.type
class WardRanking:
    ward_id: str
    ward_name: str
    current_aqi: float
    aqi_trend: str
    primary_source: str | None = None
    improvement_percent: float


@strawberry.type
class CityOverview:
    city: str
    avg_aqi: float
    max_aqi: float
    min_aqi: float
    primary_source: str
    source_breakdown: list[SourceAttribution]
    alert_level: str
    last_updated: str


@strawberry.type
class CitizenReportResult:
    report_id: str
    status: str
    message: str
