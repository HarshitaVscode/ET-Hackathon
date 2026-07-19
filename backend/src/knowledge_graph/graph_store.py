from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from src.knowledge_graph.node_types import GraphEdge, GraphNode
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class GraphStore:
    def __init__(self, persist_path: str = "backend/data/graph/graph.json"):
        self._graph = nx.MultiDiGraph()
        self._persist_path = Path(persist_path)
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._running = False

    async def start(self) -> None:
        self._load()
        self._running = True
        logger.info("GraphStore started", nodes=self._graph.number_of_nodes(), edges=self._graph.number_of_edges())

    async def stop(self) -> None:
        self._persist()
        self._running = False
        logger.info("GraphStore stopped")

    def add_node(self, node: GraphNode) -> None:
        self._graph.add_node(
            node.node_id,
            type=node.node_type.value,
            labels=node.neo4j_labels,
            **node.properties,
            created_at=node.created_at.isoformat(),
            updated_at=node.updated_at.isoformat(),
        )

    def add_edge(self, edge: GraphEdge) -> None:
        if not self._graph.has_node(edge.source_id):
            logger.warning("Source node not found", source=edge.source_id)
            return
        if not self._graph.has_node(edge.target_id):
            logger.warning("Target node not found", target=edge.target_id)
            return
        self._graph.add_edge(
            edge.source_id, edge.target_id,
            key=edge.edge_type.value,
            type=edge.edge_type.value,
            weight=edge.weight,
            created_at=edge.created_at.isoformat(),
            **edge.properties,
        )

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if not self._graph.has_node(node_id):
            return None
        data = dict(self._graph.nodes[node_id])
        data["id"] = node_id
        return data

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list[dict[str, Any]]:
        if not self._graph.has_node(node_id):
            return []
        neighbors = []
        for _, target, key, data in self._graph.edges(node_id, keys=True, data=True):
            if edge_type is None or data.get("type") == edge_type:
                node_data = dict(self._graph.nodes[target])
                node_data["id"] = target
                node_data["edge_type"] = data.get("type")
                node_data["edge_weight"] = data.get("weight", 1.0)
                neighbors.append(node_data)
        return neighbors

    def query(self, cypher_like: dict[str, Any]) -> list[dict[str, Any]]:
        node_type = cypher_like.get("type")
        limit = cypher_like.get("limit", 10)
        results = []
        for node_id, data in self._graph.nodes(data=True):
            if node_type and data.get("type") != node_type:
                continue
            entry = dict(data)
            entry["id"] = node_id
            results.append(entry)
        return results[:limit]

    def find_path(self, source_id: str, target_id: str, max_hops: int = 5) -> list[list[str]]:
        try:
            paths = list(nx.all_simple_paths(self._graph, source_id, target_id, cutoff=max_hops))
            return paths[:5]
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []

    def get_stats(self) -> dict[str, Any]:
        return {
            "nodes": self._graph.number_of_nodes(),
            "edges": self._graph.number_of_edges(),
            "node_types": self._node_type_counts(),
        }

    def _node_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for _, data in self._graph.nodes(data=True):
            t = data.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _load(self) -> None:
        if not self._persist_path.exists():
            logger.info("No existing graph to load")
            return
        try:
            with open(self._persist_path) as f:
                data = json.load(f)
            for node_id, attrs in data.get("nodes", {}).items():
                self._graph.add_node(node_id, **attrs)
            for src, dst, key, attrs in data.get("edges", []):
                self._graph.add_edge(src, dst, key=key, **attrs)
            logger.info("Graph loaded", nodes=len(data.get("nodes", {})), edges=len(data.get("edges", [])))
        except Exception:
            logger.exception("Failed to load graph")

    def _persist(self) -> None:
        data = {
            "nodes": {n: dict(d) for n, d in self._graph.nodes(data=True)},
            "edges": [
                (u, v, k, dict(d))
                for u, v, k, d in self._graph.edges(keys=True, data=True)
            ],
        }
        with open(self._persist_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Graph persisted", nodes=len(data["nodes"]), edges=len(data["edges"]))
