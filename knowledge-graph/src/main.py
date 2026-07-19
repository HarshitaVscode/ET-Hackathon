"""
Knowledge Graph Service — Entry Point.

Starts the GraphBuilder consumer and exposes a FastAPI
endpoint for graph queries used by agents and the API gateway.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from src.config import graph_config
from src.graph_builder import GraphBuilder
from src.utils.logging import get_logger

logger = get_logger(__name__)

builder = GraphBuilder()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Knowledge Graph Service")
    await builder.start()
    # Start consuming in background
    import asyncio
    asyncio.create_task(builder.consume_loop(), name="kg-consume")
    yield
    await builder.stop()
    logger.info("Knowledge Graph Service stopped")


app = FastAPI(
    title="Vayu-Drishti Knowledge Graph API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "knowledge-graph"}


@app.get("/api/v1/sources/{location_id}")
async def get_source_attribution(location_id: str) -> list[dict[str, Any]]:
    results = await builder.query_source_attribution(location_id)
    if not results:
        raise HTTPException(status_code=404, detail="No sources found for location")
    return results


@app.get("/api/v1/impact/{event_id}")
async def get_event_impact(event_id: str) -> list[dict[str, Any]]:
    results = await builder.query_impacted_wards(event_id)
    if not results:
        raise HTTPException(status_code=404, detail="Event not found or no impact data")
    return results


@app.get("/api/v1/stats")
async def graph_stats() -> dict[str, Any]:
    if not builder._driver:
        raise HTTPException(status_code=503, detail="Graph not available")
    async with builder._driver.session(database=graph_config.neo4j_database) as session:
        result = await session.run("MATCH (n) RETURN count(n) AS nodes")
        nodes = await result.single()
        result = await session.run("MATCH ()-[r]->() RETURN count(r) AS edges")
        edges = await result.single()
    return {"nodes": nodes["nodes"], "edges": edges["edges"]}


def main() -> None:
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8100, reload=True)


if __name__ == "__main__":
    main()
