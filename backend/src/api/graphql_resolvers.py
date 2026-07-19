from __future__ import annotations

from uuid import uuid4

from src.api.graphql_types import (
    AQIForecast,
    CitizenReportResult,
    CityOverview,
    SourceAttribution,
    WardRanking,
)
from src.llm_service.handler import chat as llm_chat


async def get_city_overview(city: str) -> CityOverview:
    return CityOverview(
        city=city,
        avg_aqi=285.0,
        max_aqi=412.0,
        min_aqi=180.0,
        primary_source="traffic",
        source_breakdown=[
            SourceAttribution(source_type="traffic", percentage=42.0, absolute_contribution=120.0, confidence=0.85),
            SourceAttribution(source_type="agricultural_burning", percentage=28.0, absolute_contribution=80.0, confidence=0.75),
            SourceAttribution(source_type="industry", percentage=18.0, absolute_contribution=51.0, confidence=0.70),
            SourceAttribution(source_type="construction", percentage=8.0, absolute_contribution=23.0, confidence=0.60),
            SourceAttribution(source_type="other", percentage=4.0, absolute_contribution=11.0, confidence=0.50),
        ],
        alert_level="poor",
        last_updated="2026-07-18T14:30:00Z",
    )


async def get_aqi_forecast(city: str, hours: int) -> list[AQIForecast]:
    return [
        AQIForecast(timestamp="2026-07-18T15:30:00Z", mean_aqi=280, min_aqi=250, max_aqi=310, confidence=0.95, horizon_hours=1),
        AQIForecast(timestamp="2026-07-18T17:30:00Z", mean_aqi=270, min_aqi=235, max_aqi=305, confidence=0.90, horizon_hours=3),
        AQIForecast(timestamp="2026-07-18T20:30:00Z", mean_aqi=260, min_aqi=220, max_aqi=300, confidence=0.85, horizon_hours=6),
        AQIForecast(timestamp="2026-07-19T02:30:00Z", mean_aqi=250, min_aqi=205, max_aqi=295, confidence=0.80, horizon_hours=12),
        AQIForecast(timestamp="2026-07-19T14:30:00Z", mean_aqi=230, min_aqi=175, max_aqi=285, confidence=0.70, horizon_hours=24),
        AQIForecast(timestamp="2026-07-20T14:30:00Z", mean_aqi=200, min_aqi=140, max_aqi=260, confidence=0.55, horizon_hours=48),
        AQIForecast(timestamp="2026-07-21T14:30:00Z", mean_aqi=180, min_aqi=110, max_aqi=250, confidence=0.40, horizon_hours=72),
    ][:7]


async def get_source_attribution(latitude: float, longitude: float) -> list[SourceAttribution]:
    return [
        SourceAttribution(source_type="traffic", percentage=42.0, absolute_contribution=120.0, confidence=0.85),
        SourceAttribution(source_type="agricultural_burning", percentage=28.0, absolute_contribution=80.0, confidence=0.75),
        SourceAttribution(source_type="industry", percentage=18.0, absolute_contribution=51.0, confidence=0.70),
        SourceAttribution(source_type="construction", percentage=8.0, absolute_contribution=23.0, confidence=0.60),
        SourceAttribution(source_type="other", percentage=4.0, absolute_contribution=11.0, confidence=0.50),
    ]


async def get_ward_ranking(city: str) -> list[WardRanking]:
    return [
        WardRanking(ward_id="W12", ward_name="East Delhi", current_aqi=412, aqi_trend="rising", primary_source="burning", improvement_percent=-5),
        WardRanking(ward_id="W7", ward_name="Dwarka", current_aqi=285, aqi_trend="stable", primary_source="construction", improvement_percent=0),
        WardRanking(ward_id="W4", ward_name="Vasant Kunj", current_aqi=210, aqi_trend="improving", primary_source="traffic", improvement_percent=12),
    ]


async def query_ai_assistant(query: str) -> str:
    result = await llm_chat({"query": query, "context": {}, "history": []})
    return result.get("response", "")


async def submit_citizen_report(
    latitude: float,
    longitude: float,
    report_type: str,
    description: str | None = None,
    image_urls: list[str] | None = None,
    citizen_id: str | None = None,
) -> CitizenReportResult:
    return CitizenReportResult(
        report_id=f"CR-{uuid4().hex[:8].upper()}",
        status="queued",
        message="Report submitted for verification",
    )
