"""
Resilience utilities for external API calls and stream operations.

Implements exponential backoff, circuit breaker semantics, and
graceful degradation patterns to ensure the ingestion pipeline
survives transient failures of upstream data sources.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, TypeVar
from functools import wraps
from typing import Any

from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class RetryableError(Exception):
    """Base exception for operations that should be retried."""


class NonRetryableError(Exception):
    """Exception for operations that should NOT be retried."""


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open and request is rejected."""


class CircuitBreaker:
    """Simple circuit breaker with half-open state for external service calls.

    Prevents cascading failures by stopping calls to a failing service
    and periodically probing for recovery.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_max_requests: int = 1,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.half_open_max = half_open_max_requests

        self._failure_count = 0
        self._state: str = "closed"  # closed, open, half_open
        self._last_failure_time: float | None = None
        self._half_open_requests = 0

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        if self._state == "open":
            if self._last_failure_time and (asyncio.get_event_loop().time() - self._last_failure_time) > self.recovery_timeout:
                self._state = "half_open"
                self._half_open_requests = 0
                logger.info("Circuit breaker half-open", service=self.name)
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker open for {self.name}")

        if self._state == "half_open" and self._half_open_requests >= self.half_open_max:
            raise CircuitBreakerOpenError(f"Circuit breaker half-open, max requests reached for {self.name}")

        if self._state == "half_open":
            self._half_open_requests += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"
        self._half_open_requests = 0

    def _on_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning("Circuit breaker opened", service=self.name, failures=self._failure_count)


def with_retry(
    max_attempts: int = 3,
    min_wait_seconds: float = 1.0,
    max_wait_seconds: float = 30.0,
    retryable_exceptions: tuple[type[Exception], ...] = (RetryableError, ConnectionError, TimeoutError),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator that retries async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait_seconds: Initial wait time before first retry.
        max_wait_seconds: Maximum wait time between retries.
        retryable_exceptions: Exception types that trigger a retry.

    Returns:
        Decorated async function with retry logic.
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=min_wait_seconds, max=max_wait_seconds),
                retry=retry_if_exception_type(retryable_exceptions),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            ):
                with attempt:
                    return await func(*args, **kwargs)
            raise  # pragma: no cover
        return wrapper
    return decorator
