from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from src.knowledge_graph.node_types import (
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from src.knowledge_graph.graph_store import GraphStore
from src.infrastructure.event_bus import get_event_bus
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    def __init__(self, graph_store: GraphStore) -> None:
        self._store = graph_store
        self._event_bus = get_event_bus()
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("GraphBuilder started")

    async def stop(self) -> None:
        self._running = False
        logger.info("GraphBuilder stopped")

    async def consume_loop(self) -> None:
        topics = ["raw.satellite", "raw.sensor", "raw.weather", "raw.traffic", "raw.citizen"]
        while self._running:
            for topic in topics:
                batch = await self._event_bus.consume(topic, group="graph-builder", batch_size=50)
                for record in batch:
                    try:
                        await self._process_message(topic, record["value"])
                    except Exception:
                        logger.exception("Failed to process message", topic=topic)
            await asyncio.sleep(0.1)

    async def _process_message(self, topic: str, data: dict[str, Any]) -> None:
        handlers = {
            "raw.satellite": self._handle_satellite,
            "raw.sensor": self._handle_sensor,
            "raw.weather": self._handle_weather,
            "raw.traffic": self._handle_traffic,
            "raw.citizen": self._handle_citizen,
        }
        handler = handlers.get(topic)
        if handler:
            await handler(data)

    async def _handle_satellite(self, data: dict[str, Any]) -> None:
        scene_node = GraphNode(
            node_id=f"sat:{data.get('scene_id', 'unknown')}",
            node_type=NodeType.SATELLITE_SCENE,
            properties={
                "platform": data.get("platform"),
                "acquisition_time": data.get("acquisition_time"),
                "cloud_cover": data.get("cloud_cover_percent"),
                "bbox": str(data.get("bounding_box", [])),
                "bands": data.get("bands_available", []),
            },
        )
        self._store.add_node(scene_node)

    async def _handle_sensor(self, data: dict[str, Any]) -> None:
        sensor_id = data.get("sensor_id", "unknown")
        timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

        sensor_node = GraphNode(
            node_id=f"sensor:{sensor_id}",
            node_type=NodeType.SENSOR,
            properties={
                "station_name": data.get("station_name"),
                "city": data.get("city"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "sensor_quality": data.get("sensor_quality"),
            },
        )
        self._store.add_node(sensor_node)

        reading_node = GraphNode(
            node_id=f"reading:{sensor_id}:{timestamp}",
            node_type=NodeType.SENSOR_READING,
            properties={
                "pollutant": data.get("pollutant"),
                "concentration": data.get("concentration"),
                "timestamp": timestamp,
                "unit": data.get("unit", "μg/m³"),
            },
        )
        self._store.add_node(reading_node)

        self._store.add_edge(GraphEdge(
            source_id=sensor_node.node_id,
            target_id=reading_node.node_id,
            edge_type=EdgeType.MEASURED_BY,
            properties={"timestamp": timestamp},
        ))

        pollutant = data.get("pollutant")
        if pollutant:
            pollutant_node = GraphNode(
                node_id=f"pollutant:{pollutant}:{sensor_id}",
                node_type=NodeType.POLLUTANT,
                labels=[pollutant.upper()],
                properties={
                    "name": pollutant,
                    "concentration": data.get("concentration"),
                    "timestamp": timestamp,
                },
            )
            self._store.add_node(pollutant_node)
            self._store.add_edge(GraphEdge(
                source_id=sensor_node.node_id,
                target_id=pollutant_node.node_id,
                edge_type=EdgeType.EMITS,
                properties={"concentration": data.get("concentration"), "timestamp": timestamp},
            ))

    async def _handle_weather(self, data: dict[str, Any]) -> None:
        lat = data.get("latitude", 0)
        lon = data.get("longitude", 0)
        timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

        weather_node = GraphNode(
            node_id=f"weather:{lat}:{lon}:{timestamp}",
            node_type=NodeType.WEATHER_CONDITION,
            properties={
                "source": data.get("source"),
                "temperature": data.get("temperature_celsius"),
                "humidity": data.get("relative_humidity_percent"),
                "wind_speed": data.get("wind_speed_ms"),
                "wind_direction": data.get("wind_direction_degrees"),
                "pbl_height": data.get("boundary_layer_height_m"),
                "timestamp": timestamp,
            },
        )
        self._store.add_node(weather_node)

    async def _handle_traffic(self, data: dict[str, Any]) -> None:
        segment_id = data.get("road_segment_id", "unknown")

        road_node = GraphNode(
            node_id=f"road:{segment_id}",
            node_type=NodeType.ROAD_SEGMENT,
            properties={
                "name": data.get("road_name"),
                "city": data.get("city"),
                "road_type": data.get("road_type"),
            },
        )
        self._store.add_node(road_node)

        traffic_node = GraphNode(
            node_id=f"traffic:{segment_id}:{data.get('timestamp')}",
            node_type=NodeType.TRAFFIC_FLOW,
            properties={
                "speed_kph": data.get("average_speed_kph"),
                "congestion": data.get("congestion_level"),
                "vehicle_count": data.get("vehicle_count_estimated"),
                "timestamp": data.get("timestamp"),
            },
        )
        self._store.add_node(traffic_node)

        self._store.add_edge(GraphEdge(
            source_id=road_node.node_id,
            target_id=traffic_node.node_id,
            edge_type=EdgeType.MEASURED_BY,
            properties={"timestamp": data.get("timestamp")},
        ))

    async def _handle_citizen(self, data: dict[str, Any]) -> None:
        report_id = data.get("report_id", "unknown")

        citizen_id = data.get("citizen_id", f"anon:{report_id}")
        citizen_node = GraphNode(
            node_id=f"citizen:{citizen_id}",
            node_type=NodeType.CITIZEN,
            properties={"trust_score": data.get("trust_score", 500)},
        )
        self._store.add_node(citizen_node)

        complaint_node = GraphNode(
            node_id=f"complaint:{report_id}",
            node_type=NodeType.COMPLAINT,
            properties={
                "type": data.get("report_type"),
                "description": data.get("description"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "severity": data.get("severity_rating"),
                "status": data.get("verification_status", "pending"),
                "timestamp": data.get("timestamp"),
            },
        )
        self._store.add_node(complaint_node)

        self._store.add_edge(GraphEdge(
            source_id=citizen_node.node_id,
            target_id=complaint_node.node_id,
            edge_type=EdgeType.REPORTED_BY,
        ))

    async def query_source_attribution(self, location_id: str) -> list[dict[str, Any]]:
        neighbor = self._store.get_neighbors(location_id, edge_type="AFFECTS")
        return [{"source_id": n.get("id"), "source_type": n.get("type"), "concentration": n.get("concentration")} for n in neighbor[:10]]

    async def query_impacted_wards(self, event_id: str) -> list[dict[str, Any]]:
        paths = self._store.find_path(event_id, "ward:delhi")
        return [{"path": p} for p in paths]
