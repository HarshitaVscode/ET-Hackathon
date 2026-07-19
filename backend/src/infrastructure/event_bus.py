from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class EventBus:
    def __init__(self):
        self._streams: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._running = False
        self._max_stream_length = 10000

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False

    async def publish(self, topic: str, message: dict[str, Any], key: str | None = None):
        record = {
            "id": str(uuid4()),
            "key": key or message.get("id", str(uuid4())),
            "value": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._streams[topic].append(record)
        if len(self._streams[topic]) > self._max_stream_length:
            self._streams[topic] = self._streams[topic][-self._max_stream_length // 2 :]

        for cb in self._subscribers.get(topic, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.ensure_future(cb(record))
                else:
                    cb(record)
            except Exception:
                logger.exception("EventBus callback failed for topic %s", topic)

    async def subscribe(self, topic: str, callback: Callable):
        self._subscribers[topic].append(callback)

    async def unsubscribe(self, topic: str, callback: Callable):
        if callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)

    async def consume(self, topic: str, group: str = "default", offset: int = 0, batch_size: int = 100):
        stream = self._streams.get(topic, [])
        batch = stream[offset : offset + batch_size]
        return batch

    async def get_latest(self, topic: str, n: int = 1) -> list[dict[str, Any]]:
        stream = self._streams.get(topic, [])
        return stream[-n:] if stream else []


class PubSubBroker:
    def __init__(self):
        self._topics: dict[str, list[Callable]] = defaultdict(list)

    async def publish(self, channel: str, message: Any):
        for cb in self._topics.get(channel, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.ensure_future(cb(message))
                else:
                    cb(message)
            except Exception:
                logger.exception("PubSub callback failed for channel %s", channel)

    async def subscribe(self, channel: str, callback: Callable):
        self._topics[channel].append(callback)

    async def unsubscribe(self, channel: str, callback: Callable):
        if callback in self._topics[channel]:
            self._topics[channel].remove(callback)


_event_bus: EventBus | None = None
_pubsub: PubSubBroker | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_pubsub() -> PubSubBroker:
    global _pubsub
    if _pubsub is None:
        _pubsub = PubSubBroker()
    return _pubsub
