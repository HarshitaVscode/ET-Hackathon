from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.infrastructure.event_bus import get_pubsub

websocket_router = APIRouter()

_active_connections: dict[str, list[WebSocket]] = {
    "aqi_updates": [],
    "alerts": [],
    "citizen_feed": [],
}


@websocket_router.websocket("/aqi")
async def aqi_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    _active_connections["aqi_updates"].append(websocket)
    try:
        while True:
            data = {
                "type": "aqi_update",
                "timestamp": "2026-07-18T14:30:00Z",
                "data": [
                    {"ward": "East Delhi", "aqi": 412, "pm25": 198},
                    {"ward": "Dwarka", "aqi": 285, "pm25": 128},
                ],
            }
            await websocket.send_json(data)
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        _active_connections["aqi_updates"].remove(websocket)


@websocket_router.websocket("/alerts")
async def alert_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    _active_connections["alerts"].append(websocket)
    try:
        while True:
            await websocket.send_json({
                "type": "alert",
                "severity": "warning",
                "message": "Burning detected near Ghaziabad border",
            })
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        _active_connections["alerts"].remove(websocket)


@websocket_router.websocket("/citizen")
async def citizen_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    _active_connections["citizen_feed"].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await websocket.send_json({
                "status": "received",
                "report_id": msg.get("report_id", ""),
                "message": "Report queued for verification",
            })
    except WebSocketDisconnect:
        _active_connections["citizen_feed"].remove(websocket)
