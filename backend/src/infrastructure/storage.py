from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


class LocalStorage:
    def __init__(self, base_path: str = "backend/data"):
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)
        for sub in ["satellite", "sensor", "weather", "traffic", "static", "reports"]:
            (self._base / sub).mkdir(parents=True, exist_ok=True)

    def _resolve(self, bucket: str, key: str) -> Path:
        bucket_path = self._base / bucket
        bucket_path.mkdir(parents=True, exist_ok=True)
        full_path = bucket_path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path

    async def put(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream"):
        path = self._resolve(bucket, key)
        path.write_bytes(data)
        return str(path)

    async def get(self, bucket: str, key: str) -> bytes | None:
        path = self._resolve(bucket, key)
        if not path.exists():
            return None
        return path.read_bytes()

    async def delete(self, bucket: str, key: str) -> bool:
        path = self._resolve(bucket, key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_keys(self, bucket: str, prefix: str = "") -> list[str]:
        bucket_path = self._base / bucket
        if not bucket_path.exists():
            return []
        keys = []
        for p in bucket_path.rglob(f"{prefix}*"):
            if p.is_file():
                keys.append(str(p.relative_to(bucket_path)))
        return sorted(keys)

    async def exists(self, bucket: str, key: str) -> bool:
        return self._resolve(bucket, key).exists()

    async def copy(self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str) -> str:
        src_path = self._resolve(src_bucket, src_key)
        dst_path = self._resolve(dst_bucket, dst_key)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        return str(dst_path)
