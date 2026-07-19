from __future__ import annotations


import strawberry
from strawberry.fastapi import GraphQLRouter

from src.api.graphql_types import (
    AQIForecast,
    CitizenReportResult,
    CityOverview,
    SourceAttribution,
    WardRanking,
)
from src.api.graphql_resolvers import (
    get_aqi_forecast,
    get_city_overview,
    get_source_attribution,
    get_ward_ranking,
    query_ai_assistant,
    submit_citizen_report,
)


@strawberry.type
class Query:
    @strawberry.field
    async def city_overview(self, city: str = "Delhi") -> CityOverview:
        return await get_city_overview(city)

    @strawberry.field
    async def aqi_forecast(self, city: str = "Delhi", hours: int = 72) -> list[AQIForecast]:
        return await get_aqi_forecast(city, hours)

    @strawberry.field
    async def source_attribution(self, latitude: float, longitude: float) -> list[SourceAttribution]:
        return await get_source_attribution(latitude, longitude)

    @strawberry.field
    async def ward_ranking(self, city: str = "Delhi") -> list[WardRanking]:
        return await get_ward_ranking(city)

    @strawberry.field
    async def ai_assistant(self, query: str) -> str:
        return await query_ai_assistant(query)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def report_pollution(
        self,
        latitude: float,
        longitude: float,
        report_type: str,
        description: str | None = None,
        image_urls: list[str] | None = None,
        citizen_id: str | None = None,
    ) -> CitizenReportResult:
        return await submit_citizen_report(
            latitude=latitude,
            longitude=longitude,
            report_type=report_type,
            description=description,
            image_urls=image_urls or [],
            citizen_id=citizen_id,
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema)
