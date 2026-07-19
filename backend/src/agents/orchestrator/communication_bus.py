from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from src.infrastructure.event_bus import get_pubsub
from src.infrastructure.cache import LocalCache
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class MessagePriority(Enum):
    EMERGENCY = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    ROUTINE = 5


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    ALERT = "alert"
    QUERY = "query"
    BROADCAST = "broadcast"
    DEBATE = "debate"
    VOTE = "vote"


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: uuid4().hex[:12])
    sender_id: str = ""
    target_agent: str = ""
    message_type: MessageType = MessageType.REQUEST
    payload: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    context_id: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "target_agent": self.target_agent,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "context_id": self.context_id,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        return cls(
            message_id=data.get("message_id", uuid4().hex[:12]),
            sender_id=data.get("sender_id", ""),
            target_agent=data.get("target_agent", ""),
            message_type=MessageType(data.get("message_type", "request")),
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", 5)),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            context_id=data.get("context_id", ""),
            confidence=data.get("confidence", 1.0),
        )


class CommunicationBus:
    """In-process message router for the multi-agent system.

    Agents register handlers directly. No HTTP, no Redis, no Kafka.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable] = {}
        self._subscribers: dict[str, list[Callable]] = {}
        self._agent_endpoints: dict[str, str] = {}
        self._running = False
        self._pubsub = get_pubsub()
        self._cache = LocalCache()

    def register_agent(self, agent_name: str, handler: Callable) -> None:
        self._handlers[agent_name] = handler
        logger.info("Agent registered", agent=agent_name)

    async def start(self) -> None:
        self._running = True
        logger.info("Communication bus started")

    async def stop(self) -> None:
        self._running = False
        self._handlers.clear()
        logger.info("Communication bus stopped")

    async def send_message(self, message: AgentMessage) -> dict[str, Any] | None:
        if message.message_type == MessageType.REQUEST and message.target_agent:
            return await self._send_request(message)
        elif message.message_type == MessageType.ALERT:
            await self._publish_alert(message)
            return None
        elif message.message_type == MessageType.BROADCAST:
            await self._broadcast(message)
            return None
        else:
            logger.warning("Unknown message type", type=message.message_type)
            return None

    async def _send_request(self, message: AgentMessage) -> dict[str, Any] | None:
        handler = self._handlers.get(message.target_agent)
        if not handler:
            logger.warning("Unknown target agent", agent=message.target_agent)
            return self._get_fallback(message.target_agent)

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(message.to_dict())
            else:
                result = handler(message.to_dict())
            return result
        except Exception as exc:
            logger.warning("Agent request failed", agent=message.target_agent, error=str(exc))
            return self._get_fallback(message.target_agent)

    async def _publish_alert(self, message: AgentMessage) -> None:
        await self._pubsub.publish("agent:alerts", message.to_dict())
        logger.info(
            "Alert published",
            sender=message.sender_id,
            priority=message.priority.name,
            context=message.context_id,
        )

    async def _broadcast(self, message: AgentMessage) -> None:
        results: list[dict[str, Any] | None] = []
        for agent_name in self._handlers:
            if agent_name == message.sender_id:
                continue
            msg = AgentMessage(
                sender_id=message.sender_id,
                target_agent=agent_name,
                message_type=MessageType.REQUEST,
                payload=message.payload,
                context_id=message.context_id,
            )
            result = await self._send_request(msg)
            results.append(result)
        logger.info("Broadcast complete", sender=message.sender_id, targets=len(results))

    async def resolve_conflict(
        self,
        predictions: list[dict[str, Any]],
        weights: list[float] | None = None,
    ) -> dict[str, Any]:
        if not predictions:
            return {}

        if not weights:
            weights = [p.get("confidence", 0.5) for p in predictions]

        total_weight = sum(weights)
        if total_weight == 0:
            return predictions[0]

        result: dict[str, Any] = {}
        numeric_fields = [k for k in predictions[0] if isinstance(predictions[0][k], (int, float))]
        for key in numeric_fields:
            weighted_sum = sum(
                p.get(key, 0) * w for p, w in zip(predictions, weights)
            )
            result[key] = weighted_sum / total_weight

        categorical_fields = [k for k in predictions[0] if isinstance(predictions[0][k], str)]
        for key in categorical_fields:
            values = [p.get(key, "") for p in predictions]
            result[key] = Counter(values).most_common(1)[0][0]

        result["confidence"] = max(w / total_weight for w in weights) if weights else 0.5
        result["consensus_method"] = "confidence_weighted_vote"
        return result

    def _get_fallback(self, agent_name: str) -> dict[str, Any] | None:
        fallbacks = {
            "aqi_forecast": {"aqi_predicted": 0, "confidence": 0.0, "is_fallback": True, "source_agent": agent_name},
            "source_attribution": {"contributions": {}, "confidence": 0.0, "is_fallback": True, "source_agent": agent_name},
            "burn_detection": {"detections": [], "confidence": 0.0, "is_fallback": True, "source_agent": agent_name},
        }
        return fallbacks.get(agent_name)
