from __future__ import annotations

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff ** attempt)
                        logger.warning(f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {exc}")
                        await asyncio.sleep(wait)
            raise last_exc
        return wrapper
    return decorator


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self._failures = 0
        self._last_failure_time = 0.0
        self._state = "closed"

    async def call(self, func: Callable, *args, **kwargs):
        if self._state == "open":
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = "half-open"
            else:
                raise Exception(f"Circuit breaker {self.name} is open")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._failures = 0
            self._state = "closed"
            return result
        except Exception as exc:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.failure_threshold:
                self._state = "open"
            raise exc
