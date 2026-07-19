from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from src.infrastructure.event_bus import get_event_bus
from src.infrastructure.storage import LocalStorage
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectorStatus(Enum):
    INITIALIZED = "initialized"
    CONNECTED = "connected"
    RUNNING = "running"
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class BaseConnector(ABC):
    def __init__(self, connector_name: str) -> None:
        self.name = connector_name
        self.status = ConnectorStatus.INITIALIZED
        self._running = False
        self._poll_task: asyncio.Task[None] | None = None
        self._event_bus = get_event_bus()
        self._storage = LocalStorage("backend/data")

    async def initialize(self) -> None:
        logger.info("Initializing connector", connector=self.name)
        try:
            self._validate_config()
            await self._connect_source()
            self.status = ConnectorStatus.CONNECTED
            logger.info("Connector initialized", connector=self.name)
        except Exception:
            logger.exception("Connector initialization failed", connector=self.name)
            self.status = ConnectorStatus.FAILED
            raise

    async def start_polling(self, interval_seconds: float = 300.0) -> None:
        if self._running:
            logger.warning("Connector already running", connector=self.name)
            return
        self._running = True
        self.status = ConnectorStatus.RUNNING
        self._poll_task = asyncio.create_task(
            self._poll_loop(interval_seconds),
            name=f"{self.name}-poll",
        )
        logger.info("Polling started", connector=self.name, interval=interval_seconds)

    async def stop(self) -> None:
        self._running = False
        self.status = ConnectorStatus.DISCONNECTED
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        await self._disconnect_source()
        logger.info("Connector stopped", connector=self.name)

    async def _poll_loop(self, interval: float) -> None:
        while self._running:
            try:
                batch = await self._fetch_batch()
                if batch:
                    await self._produce_batch(batch)
                else:
                    logger.debug("Empty batch", connector=self.name)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Poll error", connector=self.name)
                self.status = ConnectorStatus.FAILED
                await asyncio.sleep(interval)
                self.status = ConnectorStatus.RUNNING
                continue
            await asyncio.sleep(interval)

    async def _produce_batch(self, messages: list[Any]) -> None:
        topic = self._get_topic()
        for msg in messages:
            key = self._get_message_key(msg)
            value = self._serialize_message(msg)
            if value is None:
                continue
            payload = json.loads(value) if isinstance(value, bytes) else value
            await self._event_bus.publish(topic=topic, message=payload, key=key)
        logger.debug("Produced batch", connector=self.name, topic=topic, count=len(messages))

    @abstractmethod
    def _validate_config(self) -> None:
        ...

    @abstractmethod
    async def _connect_source(self) -> None:
        ...

    @abstractmethod
    async def _disconnect_source(self) -> None:
        ...

    @abstractmethod
    async def _fetch_batch(self) -> list[Any]:
        ...

    @abstractmethod
    def _serialize_message(self, message: Any) -> bytes | None:
        ...

    @abstractmethod
    def _get_topic(self) -> str:
        ...

    @abstractmethod
    def _get_message_key(self, message: Any) -> str:
        ...
