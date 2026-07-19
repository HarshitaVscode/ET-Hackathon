"""
Agent Communication Bus — Message passing between all AI agents.

Implements five communication patterns:
1. REQUEST-RESPONSE: Direct agent-to-agent query
2. PUBLISH-SUBSCRIBE: One agent broadcasts to all subscribers
3. CHAIN: Multi-hop reasoning (A → B → C → A)
4. DEBATE: Two agents resolve conflicting predictions
5. VOTE: Multiple agents weighted voting for consensus

Uses protobuf for message serialization and Redis for pub/sub.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine
from uuid import uuid4

import httpx
from redis.asyncio import Redis

from agents.orchestrator.src.config import orchestrator_config
from agents.orchestrator.src.utils.logging import get_logger

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
    """Universal message format for inter-agent communication."""
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
    """Central message router for the multi-agent system.

    Agents register with the bus, subscribe to topics,
    and send/receive messages through this service.
    """

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._http_clients: dict[str, httpx.AsyncClient] = {}
        self._subscribers: dict[str, list[Callable[[AgentMessage], Coroutine[Any, Any, None]]]] = {}
        self._pending_responses: dict[str, asyncio.Future] = {}
        self._agent_endpoints: dict[str, str] = {}
        self._running = False

    async def start(self) -> None:
        """Initialize Redis connection and start subscriber."""
        self._redis = Redis(
            host=orchestrator_config.redis_host,
            port=orchestrator_config.redis_port,
            db=orchestrator_config.redis_db,
            decode_responses=True,
        )

        for agent_name, cfg in orchestrator_config.agent_configs.items():
            self._agent_endpoints[agent_name] = cfg["endpoint"]
            self._http_clients[agent_name] = httpx.AsyncClient(
                base_url=cfg["endpoint"],
                timeout=httpx.Timeout(cfg["timeout"]),
            )

        self._running = True
        logger.info("Communication bus started")

    async def send_message(self, message: AgentMessage) -> dict[str, Any] | None:
        """Send a message to a target agent and optionally wait for response."""
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
        """Send a request to a specific agent and await response."""
        endpoint = self._agent_endpoints.get(message.target_agent)
        if not endpoint:
            logger.warning("Unknown target agent", agent=message.target_agent)
            return None

        client = self._http_clients.get(message.target_agent)
        if not client:
            return None

        try:
            response = await client.post(
                "/api/v1/process",
                json={
                    "message": message.to_dict(),
                    "context_id": message.context_id,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", result)
        except httpx.TimeoutException:
            logger.warning("Agent timeout", agent=message.target_agent)
            return self._get_fallback(message.target_agent)
        except Exception as exc:
            logger.warning("Agent request failed", agent=message.target_agent, error=str(exc))
            return self._get_fallback(message.target_agent)

    async def _publish_alert(self, message: AgentMessage) -> None:
        """Publish an alert to all agents via Redis pub/sub."""
        if not self._redis:
            return
        await self._redis.publish(
            "agent:alerts",
            json.dumps(message.to_dict()),
        )
        logger.info(
            "Alert published",
            sender=message.sender_id,
            priority=message.priority.name,
            context=message.context_id,
        )

    async def _broadcast(self, message: AgentMessage) -> None:
        """Broadcast a message to all registered agents."""
        results: list[dict[str, Any] | None] = []
        for agent_name in self._agent_endpoints:
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
        """Resolve conflicting predictions using confidence-weighted voting."""
        if not predictions:
            return {}

        if not weights:
            weights = [p.get("confidence", 0.5) for p in predictions]

        total_weight = sum(weights)
        if total_weight == 0:
            return predictions[0]

        # Weighted average for numeric fields
        result: dict[str, Any] = {}
        numeric_fields = [k for k in predictions[0] if isinstance(predictions[0][k], (int, float))]
        for key in numeric_fields:
            weighted_sum = sum(
                p.get(key, 0) * w for p, w in zip(predictions, weights)
            )
            result[key] = weighted_sum / total_weight

        # Majority vote for categorical fields
        categorical_fields = [k for k in predictions[0] if isinstance(predictions[0][k], str)]
        for key in categorical_fields:
            from collections import Counter
            values = [p.get(field, "") for p in predictions]
            result[field] = Counter(values).most_common(1)[0][0]

        result["confidence"] = max(w / total_weight for w in weights) if weights else 0.5
        result["consensus_method"] = "confidence_weighted_vote"
        return result

    def _get_fallback(self, agent_name: str) -> dict[str, Any] | None:
        """Return fallback response when an agent is unavailable."""
        cfg = orchestrator_config.agent_configs.get(agent_name)
        if cfg:
            fallback = dict(cfg.get("fallback", {}))
            fallback["is_fallback"] = True
            fallback["source_agent"] = agent_name
            return fallback
        return None

    async def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        for client in self._http_clients.values():
            await client.aclose()
        if self._redis:
            await self._redis.close()
        logger.info("Communication bus stopped")
