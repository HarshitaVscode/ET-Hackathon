from __future__ import annotations

import json
import time
from collections import OrderedDict
from typing import Any


class LocalCache:
    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int | None = None):
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry)
        self._cache.move_to_end(key)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def delete(self, key: str):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def exists(self, key: str) -> bool:
        return self.get(key) is not None
