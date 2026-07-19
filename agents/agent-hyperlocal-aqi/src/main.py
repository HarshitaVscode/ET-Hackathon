from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.agent_hyperlocal_aqi.src.config import AgentConfig
from agents.agent_hyperlocal_aqi.src.handler import initialize, process_request

app = FastAPI(title="Hyperlocal AQI Forecast Agent", version="1.0.0")
config = AgentConfig()


class ForecastRequest(BaseModel):
    location_id: Optional[int] = None
    steps: int = 72


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


@app.on_event("startup")
def startup() -> None:
    initialize(config.artifacts_dir)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    from agents.agent_hyperlocal_aqi.src.handler import _forecaster
    return HealthResponse(
        status="ok",
        model_loaded=_forecaster is not None and _forecaster.is_loaded,
    )


@app.post("/api/v1/process")
def process(req: ForecastRequest) -> dict:
    try:
        result = process_request({"location_id": req.location_id, "steps": req.steps})
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/locations")
def list_locations() -> list[dict]:
    from agents.agent_hyperlocal_aqi.src.handler import _forecaster
    if _forecaster is None or not _forecaster.is_loaded:
        return []
    return [
        {"location_id": lid, **meta}
        for lid, meta in _forecaster._location_metadata.items()
    ]


@app.get("/api/v1/forecast/{location_id}")
def get_forecast(location_id: int, steps: int = 72) -> dict:
    try:
        result = process_request({"location_id": location_id, "steps": steps})
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
