from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import config
from src.api.rest import router as rest_router
from src.api.graphql_schema import graphql_router
from src.api.websocket import websocket_router

from src.infrastructure.event_bus import get_event_bus, get_pubsub
from src.infrastructure.database import TimeseriesDB
from src.infrastructure.vector_store import VectorStore
from src.infrastructure.storage import LocalStorage
from src.infrastructure.cache import LocalCache

from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.graph_builder import GraphBuilder
from src.agents.orchestrator.communication_bus import CommunicationBus

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)

event_bus = get_event_bus()
pubsub = get_pubsub()
db = TimeseriesDB("backend/data/vayu.db")
vector_store = VectorStore("backend/data/embeddings")
storage = LocalStorage("backend/data")
cache = LocalCache()
graph_store = GraphStore("backend/data/graph/graph.json")
graph_builder = GraphBuilder(graph_store)
orchestrator_bus = CommunicationBus()

_traffic_opt: Any = None
_squad_router: Any = None
_emergency_opt: Any = None
_llm_handler: Any = None
_ingestion_tasks: list[asyncio.Task] = []


def _register_agents():
    from src.agents.aqi_forecast.handler import initialize as init_aqi, process_request as aqi_handler
    from src.agents.source_attribution.handler import initialize as init_attr, process_request as attr_handler
    from src.agents.burn_detection.handler import initialize as init_burn, process_request as burn_handler
    from src.decision_engine.handler import initialize as init_decision, optimize_traffic, assess_emergency

    global _traffic_opt, _squad_router, _emergency_opt, _llm_handler

    init_aqi()
    init_attr()
    init_burn()
    init_decision()

    orchestrator_bus.register_agent("aqi_forecast", aqi_handler)
    orchestrator_bus.register_agent("source_attribution", attr_handler)
    orchestrator_bus.register_agent("burn_detection", burn_handler)

    async def traffic_handler(msg):
        return await optimize_traffic(msg.get("payload", msg))

    async def emergency_handler(msg):
        return await assess_emergency(msg.get("payload", msg))

    orchestrator_bus.register_agent("traffic_monitor", traffic_handler)
    orchestrator_bus.register_agent("emergency_response", emergency_handler)

    from src.llm_service.handler import chat as llm_chat
    _llm_handler = llm_chat

    logger.info("All agents registered")


async def _start_ingestion():
    try:
        from src.ingestion.connectors.caaqms_connector import CAAQMSConnector
        from src.ingestion.connectors.satellite_connector import SatelliteConnector
        from src.ingestion.connectors.weather_connector import WeatherConnector
        from src.ingestion.connectors.traffic_connector import TrafficConnector
        from src.ingestion.connectors.citizen_connector import CitizenConnector

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
                logger.info("Connector initialized", name=name)
            except Exception:
                logger.exception("Connector failed to initialize", name=name)

        polling_intervals = {
            "caaqms": config.cpcb_poll_interval_seconds,
            "satellite": 3600,
            "weather": config.imd_poll_interval_hours * 3600,
            "traffic": config.google_traffic_poll_interval_seconds,
        }

        for name, interval in polling_intervals.items():
            conn = connectors.get(name)
            if conn:
                task = asyncio.create_task(conn.start_polling(interval_seconds=interval))
                _ingestion_tasks.append(task)

        logger.info("Ingestion layer started")
    except Exception:
        logger.exception("Failed to start ingestion layer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {config.app_name} v0.1.0")
    logger.info(f"Mode: {config.app_env}")

    await event_bus.start()
    db.connect()
    await graph_store.start()
    await graph_builder.start()
    await orchestrator_bus.start()

    _register_agents()

    asyncio.create_task(graph_builder.consume_loop(), name="graph-builder")

    await _start_ingestion()

    logger.info("All services initialized")
    yield

    logger.info("Shutting down...")
    for task in _ingestion_tasks:
        task.cancel()
    await orchestrator_bus.stop()
    await graph_builder.stop()
    await graph_store.stop()
    db.close()
    await event_bus.stop()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Vayu-Drishti API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_router, prefix="/graphql")
app.include_router(rest_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/ws")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": config.app_name}


@app.get("/api/v1/workflow/standard")
async def trigger_standard_workflow() -> dict[str, Any]:
    from src.agents.orchestrator.state_machine import build_standard_workflow
    dag = build_standard_workflow(orchestrator_bus)
    result = await dag.execute()
    return result


@app.get("/api/v1/workflow/emergency")
async def trigger_emergency_workflow() -> dict[str, Any]:
    from src.agents.orchestrator.state_machine import build_emergency_workflow
    dag = build_emergency_workflow(orchestrator_bus)
    result = await dag.execute()
    return result


@app.post("/api/v1/chat")
async def chat(request: dict[str, Any]) -> dict[str, Any]:
    return await _llm_handler(request)


@app.get("/api/v1/graph/stats")
async def graph_stats() -> dict[str, Any]:
    return graph_store.get_stats()


@app.get("/api/v1/db/stats")
async def db_stats() -> dict[str, Any]:
    return {"status": "connected", "path": "backend/data/vayu.db"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> JSONResponse:
    import time
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000))
    return response
