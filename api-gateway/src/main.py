"""
API Gateway — Entry Point.

Unified REST + GraphQL gateway for Vayu-Drishti.
Routes requests to the appropriate microservice,
handles authentication, rate limiting, and response caching.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import gateway_config
from src.graphql.schema import graphql_router
from src.rest.routes import router as rest_router
from src.websocket.handlers import websocket_router

logger = __import__("structlog").get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API Gateway")
    yield
    logger.info("API Gateway stopped")


app = FastAPI(
    title="Vayu-Drishti API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sub-routers
app.include_router(graphql_router, prefix="/graphql")
app.include_router(rest_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/ws")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "api-gateway"}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> JSONResponse:
    import time
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000))
    return response


def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=gateway_config.app_port,
        reload=gateway_config.app_debug,
    )


if __name__ == "__main__":
    main()
