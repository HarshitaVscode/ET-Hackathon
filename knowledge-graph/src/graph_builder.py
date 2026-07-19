"""
Knowledge Graph Builder — Consumes Kafka messages and updates Neo4j.

This is the central graph maintenance service. It listens to all
ingestion topics and translates events into graph nodes and edges,
maintaining the semantic web of urban air quality relationships.

Designed for high throughput using batch Cypher operations.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import aiokafka
from neo4j import AsyncDriver, AsyncGraphDatabase
from redis.asyncio import Redis

from src.config import graph_config
from src.models.node_types import (
    CYPHER_CREATE_CONSTRAINTS,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GraphBuilder:
    """Consumes Kafka topics and maintains the Neo4j knowledge graph.

    Responsibilities:
    - Subscribe to all raw data topics
    - Parse messages into GraphNode/GraphEdge objects
    - Batch-upsert into Neo4j
    - Cache frequently queried subgraphs in Redis
    - Emit graph-update events for downstream agents
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None
        self._redis: Redis | None = None
        self._consumer: aiokafka.AIOKafkaConsumer | None = None
        self._running = False

    async def start(self) -> None:
        """Initialize connections and start consuming."""
        self._driver = AsyncGraphDatabase.driver(
            graph_config.neo4j_uri,
            auth=(graph_config.neo4j_user, graph_config.neo4j_password),
            max_connection_lifetime=3600,
            connection_timeout=15,
        )
        self._redis = Redis(
            host=graph_config.redis_host,
            port=graph_config.redis_port,
            db=graph_config.redis_db,
            decode_responses=True,
        )

        await self._initialize_schema()

        self._consumer = aiokafka.AIOKafkaConsumer(
            graph_config.kafka_satellite_topic,
            graph_config.kafka_sensor_topic,
            graph_config.kafka_weather_topic,
            graph_config.kafka_traffic_topic,
            graph_config.kafka_citizen_topic,
            bootstrap_servers=graph_config.kafka_broker_list,
            group_id=graph_config.kafka_consumer_group,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            max_poll_records=500,
        )
        await self._consumer.start()
        self._running = True

        logger.info("GraphBuilder started")

    async def _initialize_schema(self) -> None:
        """Create Neo4j constraints and indexes."""
        if not self._driver:
            return
        async with self._driver.session(database=graph_config.neo4j_database) as session:
            for statement in CYPHER_CREATE_CONSTRAINTS.split(";"):
                stmt = statement.strip()
                if stmt:
                    await session.run(stmt)
        logger.info("Graph schema initialized")

    async def consume_loop(self) -> None:
        """Main consumption loop — processes messages from all topics."""
        if not self._consumer:
            return

        while self._running:
            try:
                batch = await self._consumer.getmany(timeout_ms=1000, max_records=500)
                for topic, messages in batch.items():
                    operations: list[tuple[str, dict[str, Any]]] = []
                    for msg in messages:
                        ops = await self._process_message(topic, msg)
                        operations.extend(ops)
                    if operations:
                        await self._execute_batch(operations)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in consume loop")
                await asyncio.sleep(1)

    async def _process_message(
        self, topic: str, msg: aiokafka.ConsumerRecord
    ) -> list[tuple[str, dict[str, Any]]]:
        """Parse a Kafka message and return Cypher operations."""
        try:
            data = json.loads(msg.value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid message on topic", topic=topic)
            return []

        topic_handlers = {
            graph_config.kafka_satellite_topic: self._handle_satellite,
            graph_config.kafka_sensor_topic: self._handle_sensor,
            graph_config.kafka_weather_topic: self._handle_weather,
            graph_config.kafka_traffic_topic: self._handle_traffic,
            graph_config.kafka_citizen_topic: self._handle_citizen,
        }
        handler = topic_handlers.get(topic)
        if not handler:
            return []

        try:
            return await handler(data)
        except Exception:
            logger.exception("Handler failed", topic=topic)
            return []

    async def _handle_satellite(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        ops: list[tuple[str, dict[str, Any]]] = []

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
        ops.append(scene_node.to_cypher_create())

        # Link scene to city
        bbox = data.get("bounding_box", [])
        if len(bbox) == 4:
            city_edge = GraphEdge(
                source_id=scene_node.node_id,
                target_id="city:delhi",
                edge_type=EdgeType.CONTAINS,
            )
            ops.append(city_edge.to_cypher_create())

        return ops

    async def _handle_sensor(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        ops: list[tuple[str, dict[str, Any]]] = []
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
        ops.append(sensor_node.to_cypher_create())

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
        ops.append(reading_node.to_cypher_create())

        reading_edge = GraphEdge(
            source_id=sensor_node.node_id,
            target_id=reading_node.node_id,
            edge_type=EdgeType.MEASURED_BY,
            properties={"timestamp": timestamp},
        )
        ops.append(reading_edge.to_cypher_create())

        # Pollutant node
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
            ops.append(pollutant_node.to_cypher_create())

            emit_edge = GraphEdge(
                source_id=sensor_node.node_id,
                target_id=pollutant_node.node_id,
                edge_type=EdgeType.EMITS,
                properties={"concentration": data.get("concentration"), "timestamp": timestamp},
            )
            ops.append(emit_edge.to_cypher_create())

        return ops

    async def _handle_weather(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        ops: list[tuple[str, dict[str, Any]]] = []
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
        ops.append(weather_node.to_cypher_create())
        return ops

    async def _handle_traffic(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        ops: list[tuple[str, dict[str, Any]]] = []
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
        ops.append(road_node.to_cypher_create())

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
        ops.append(traffic_node.to_cypher_create())

        traffic_edge = GraphEdge(
            source_id=road_node.node_id,
            target_id=traffic_node.node_id,
            edge_type=EdgeType.MEASURED_BY,
            properties={"timestamp": data.get("timestamp")},
        )
        ops.append(traffic_edge.to_cypher_create())

        return ops

    async def _handle_citizen(self, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        ops: list[tuple[str, dict[str, Any]]] = []
        report_id = data.get("report_id", "unknown")

        citizen_id = data.get("citizen_id", f"anon:{report_id}")
        citizen_node = GraphNode(
            node_id=f"citizen:{citizen_id}",
            node_type=NodeType.CITIZEN,
            properties={"trust_score": data.get("trust_score", 500)},
        )
        ops.append(citizen_node.to_cypher_create())

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
        ops.append(complaint_node.to_cypher_create())

        report_edge = GraphEdge(
            source_id=citizen_node.node_id,
            target_id=complaint_node.node_id,
            edge_type=EdgeType.REPORTED_BY,
        )
        ops.append(report_edge.to_cypher_create())

        return ops

    async def _execute_batch(self, operations: list[tuple[str, dict[str, Any]]]) -> None:
        """Execute batch Cypher operations in a single transaction."""
        if not operations or not self._driver:
            return
        async with self._driver.session(database=graph_config.neo4j_database) as session:
            async with session.begin_transaction() as tx:
                for query, params in operations:
                    try:
                        await tx.run(query, **params)
                    except Exception:
                        logger.warning("Cypher operation failed", query=query[:100])
            await session.commit()

    async def query_impacted_wards(self, event_id: str) -> list[dict[str, Any]]:
        """Query which wards are impacted by a pollution event."""
        from src.models.node_types import CYPHER_FIND_IMPACTED_WARDS
        if not self._driver:
            return []
        async with self._driver.session(database=graph_config.neo4j_database) as session:
            result = await session.run(CYPHER_FIND_IMPACTED_WARDS, event_id=event_id)
            return [record.data() async for record in result]

    async def query_source_attribution(self, location_id: str) -> list[dict[str, Any]]:
        """Query pollution sources affecting a location."""
        from src.models.node_types import CYPHER_FIND_SOURCES_AFFECTING_LOCATION
        if not self._driver:
            return []
        async with self._driver.session(database=graph_config.neo4j_database) as session:
            result = await session.run(CYPHER_FIND_SOURCES_AFFECTING_LOCATION, location_id=location_id)
            return [record.data() async for record in result]

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._driver:
            await self._driver.close()
        if self._redis:
            await self._redis.close()
        logger.info("GraphBuilder stopped")
