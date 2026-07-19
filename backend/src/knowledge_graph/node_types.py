from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    CITY = "City"
    WARD = "Ward"
    LOCATION = "Location"
    SENSOR = "Sensor"
    SENSOR_READING = "SensorReading"
    INDUSTRY = "Industry"
    ROAD_SEGMENT = "RoadSegment"
    CONSTRUCTION_SITE = "ConstructionSite"
    BURNING_EVENT = "BurningEvent"
    POLLUTION_EVENT = "PollutionEvent"
    POLLUTANT = "Pollutant"
    SOURCE_TYPE = "SourceType"
    CITIZEN = "Citizen"
    COMPLAINT = "Complaint"
    ENFORCEMENT_ACTION = "EnforcementAction"
    HEALTH_OUTCOME = "HealthOutcome"
    TRAFFIC_FLOW = "TrafficFlow"
    WEATHER_CONDITION = "WeatherCondition"
    POLICY_ACTION = "PolicyAction"
    SATELLITE_SCENE = "SatelliteScene"


class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    MEASURED_BY = "MEASURED_BY"
    EMITS = "EMITS"
    AFFECTS = "AFFECTS"
    CAUSED_BY = "CAUSED_BY"
    LOCATED_AT = "LOCATED_AT"
    REPORTED_BY = "REPORTED_BY"
    VERIFIED_BY = "VERIFIED_BY"
    TRIGGERS = "TRIGGERS"
    MITIGATES = "MITIGATES"
    CORRELATES_WITH = "CORRELATES_WITH"
    TRANSPORTED_BY = "TRANSPORTED_BY"
    EXCEEDS_THRESHOLD = "EXCEEDS_THRESHOLD"
    HAS_PROPERTY = "HAS_PROPERTY"
    NEAR = "NEAR"
    UPWIND_OF = "UPWIND_OF"
    PREDICTED_BY = "PREDICTED_BY"


@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    labels: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def neo4j_labels(self) -> list[str]:
        return [self.node_type.value] + self.labels


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
