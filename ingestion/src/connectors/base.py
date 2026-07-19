"""
Abstract base class for all data source connectors.

Defines the lifecycle contract that every connector must follow:
initialize → connect → poll → produce → disconnect.

Uses the Template Method pattern for the main loop and the
Strategy pattern for pluggable serialization backends.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from aiokafka import AIOKafkaProducer
from src.config import config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectorStatus(Enum):
    INITIALIZED = "initialized"
    CONNECTED = "connected"
    RUNNING = "running"
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class BaseConnector(ABC):
    """Template for all data source connectors.

    Subclasses must implement:
    - _validate_config()
    - _connect_source()
    - _disconnect_source()
    - _fetch_batch()
    - _serialize_message()
    - _get_topic()
    """

    def __init__(self, connector_name: str) -> None:
        self.name = connector_name
        self.status = ConnectorStatus.INITIALIZED
        self._kafka_producer: AIOKafkaProducer | None = None
        self._running = False
        self._poll_task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        """Validate config and prepare resources. Never raises on expected failures."""
        logger.info("Initializing connector", connector=self.name)
        try:
            self._validate_config()
            self._kafka_producer = AIOKafkaProducer(
                bootstrap_servers=config.kafka_broker_list,
                client_id=f"vayu-{self.name}",
                max_request_size=10485760,  # 10MB
                compression_type="gzip",
            )
            await self._kafka_producer.start()
            self.status = ConnectorStatus.CONNECTED
            logger.info("Connector initialized", connector=self.name)
        except Exception:
            logger.exception("Connector initialization failed", connector=self.name)
            self.status = ConnectorStatus.FAILED
            raise

    async def start_polling(self, interval_seconds: float = 300.0) -> None:
        """Start the polling loop in a background task."""
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
        """Gracefully stop polling and disconnect."""
        self._running = False
        self.status = ConnectorStatus.DISCONNECTED
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        await self._disconnect_source()
        if self._kafka_producer:
            await self._kafka_producer.stop()
        logger.info("Connector stopped", connector=self.name)

    async def _poll_loop(self, interval: float) -> None:
        """Main polling loop."""
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
                # Continue running despite transient failures
                await asyncio.sleep(interval)
                self.status = ConnectorStatus.RUNNING
                continue
            await asyncio.sleep(interval)

    async def _produce_batch(self, messages: list[Any]) -> None:
        """Serialize and produce a batch of messages to Kafka."""
        if not self._kafka_producer:
            raise RuntimeError("Kafka producer not initialized")
        topic = self._get_topic()
        for msg in messages:
            key = self._get_message_key(msg)
            value = self._serialize_message(msg)
            if value is None:
                continue
            await self._kafka_producer.send(
                topic=topic,
                key=key.encode("utf-8") if isinstance(key, str) else key,
                value=value,
            )
        logger.debug("Produced batch", connector=self.name, topic=topic, count=len(messages))

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate source-specific configuration."""

    @abstractmethod
    async def _connect_source(self) -> None:
        """Establish connection to the data source."""

    @abstractmethod
    async def _disconnect_source(self) -> None:
        """Tear down the data source connection."""

    @abstractmethod
    async def _fetch_batch(self) -> list[Any]:
        """Fetch the next batch of records from the source."""

    @abstractmethod
    def _serialize_message(self, message: Any) -> bytes | None:
        """Serialize a message to bytes for Kafka."""

    @abstractmethod
    def _get_topic(self) -> str:
        """Return the Kafka topic name for this connector."""

    @abstractmethod
    def _get_message_key(self, message: Any) -> str:
        """Return the Kafka message key for partitioning."""
