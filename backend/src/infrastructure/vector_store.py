from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


class VectorStore:
    def __init__(self, persist_dir: str = "backend/data/embeddings"):
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._collections: dict[str, dict[str, Any]] = {}

    def create_collection(self, name: str, vector_size: int = 768):
        if name not in self._collections:
            self._collections[name] = {
                "vector_size": vector_size,
                "vectors": [],
                "metadata": [],
                "ids": [],
            }

    def upsert(self, collection: str, ids: list[str], vectors: list[list[float]], metadata: list[dict[str, Any]] | None = None):
        if collection not in self._collections:
            self.create_collection(collection, len(vectors[0]) if vectors else 768)
        col = self._collections[collection]
        meta = metadata or [{}] * len(ids)
        for i, (vid, vec, m) in enumerate(zip(ids, vectors, meta)):
            if vid in col["ids"]:
                idx = col["ids"].index(vid)
                col["vectors"][idx] = vec
                col["metadata"][idx] = m
            else:
                col["ids"].append(vid)
                col["vectors"].append(vec)
                col["metadata"].append(m)

    def search(self, collection: str, query_vector: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        if collection not in self._collections:
            return []
        col = self._collections[collection]
        if not col["vectors"]:
            return []

        query = np.array(query_vector, dtype=np.float32)
        vectors = np.array(col["vectors"], dtype=np.float32)

        norms = np.linalg.norm(vectors, axis=1)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        similarities = np.dot(vectors, query) / (norms * query_norm + 1e-10)

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                "id": col["ids"][idx],
                "score": float(similarities[idx]),
                "metadata": col["metadata"][idx],
            })
        return results

    def delete(self, collection: str, ids: list[str]):
        if collection not in self._collections:
            return
        col = self._collections[collection]
        for vid in ids:
            if vid in col["ids"]:
                idx = col["ids"].index(vid)
                col["ids"].pop(idx)
                col["vectors"].pop(idx)
                col["metadata"].pop(idx)

    def persist(self):
        for name, col in self._collections.items():
            filepath = self._persist_dir / f"{name}.json"
            data = {
                "vector_size": col["vector_size"],
                "ids": col["ids"],
                "vectors": [[float(v) for v in vec] for vec in col["vectors"]],
                "metadata": col["metadata"],
            }
            with open(filepath, "w") as f:
                json.dump(data, f)

    def load(self):
        for filepath in self._persist_dir.glob("*.json"):
            with open(filepath) as f:
                data = json.load(f)
            name = filepath.stem
            self._collections[name] = {
                "vector_size": data["vector_size"],
                "ids": data["ids"],
                "vectors": [np.array(v, dtype=np.float32) for v in data["vectors"]],
                "metadata": data["metadata"],
            }

    def count(self, collection: str) -> int:
        if collection not in self._collections:
            return 0
        return len(self._collections[collection]["ids"])
