from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class CausalDAGLearner:
    def __init__(self) -> None:
        self.graph: nx.DiGraph | None = None
        self.scaler = StandardScaler()
        self.node_names: list[str] = []
        self._causal_effects: dict[str, float] = {}

    def learn_structure(self, data: pd.DataFrame) -> nx.DiGraph:
        self.node_names = list(data.columns)
        scaled_data = pd.DataFrame(
            self.scaler.fit_transform(data),
            columns=self.node_names,
        )

        try:
            from causalnex.structure import StructureModel
            from causalnex.structure.notears import from_pandas

            sm = from_pandas(scaled_data)
            self.graph = sm

            while True:
                try:
                    cycles = list(nx.simple_cycles(self.graph))
                    if not cycles:
                        break
                    for cycle in cycles:
                        min_edge = min(
                            [(u, v) for u, v in zip(cycle, cycle[1:] + [cycle[0]])],
                            key=lambda e: abs(self.graph.edges[e].get("weight", 0)),
                        )
                        self.graph.remove_edge(*min_edge)
                except nx.NetworkXNoCycle:
                    break

        except ImportError:
            logger.warning("causalnex not available, using correlation-based DAG")
            self.graph = self._build_correlation_dag(scaled_data)

        self._compute_causal_effects(data)
        return self.graph

    def _build_correlation_dag(self, data: pd.DataFrame) -> nx.DiGraph:
        G = nx.DiGraph()
        for col in data.columns:
            G.add_node(col)
        corr = data.corr(method="spearman")
        for i, src in enumerate(data.columns):
            for j, dst in enumerate(data.columns):
                if i != j and abs(corr.iloc[i, j]) > 0.15:
                    if corr.iloc[i, j] > 0:
                        G.add_edge(src, dst, weight=abs(corr.iloc[i, j]))
        return G

    def _compute_causal_effects(self, data: pd.DataFrame) -> None:
        if self.graph is None:
            return
        aqi_cols = [c for c in data.columns if "aqi" in c.lower() or "pm" in c.lower()]
        if not aqi_cols:
            aqi_cols = [data.columns[-1]]
        target = aqi_cols[0]
        sources = [c for c in data.columns if c not in aqi_cols]
        for source in sources:
            if self.graph.has_edge(source, target):
                X = data[source].values.reshape(-1, 1)
                y = data[target].values
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(X, y)
                self._causal_effects[source] = float(model.coef_[0])

    def attribute_sources(self, current_data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        if self.graph is None or not self._causal_effects:
            return self._fallback_attribution(current_data)
        contributions: dict[str, dict[str, Any]] = {}
        total_aqi = current_data.get("aqi") or current_data.get("pm2_5", [0])[0]
        for source in self.node_names:
            if source in self._causal_effects:
                effect = self._causal_effects[source]
                source_val = float(current_data[source].iloc[0]) if hasattr(current_data, 'iloc') else float(current_data[source])
                contrib = effect * source_val
                contributions[source] = {
                    "source_type": source,
                    "absolute_contribution": abs(contrib),
                    "percentage": float(abs(contrib) / max(abs(total_aqi), 1) * 100),
                    "causal_effect": effect,
                    "confidence": min(1.0, abs(effect) / 2.0),
                }
        total_pct = sum(c["percentage"] for c in contributions.values())
        if total_pct > 0:
            for c in contributions.values():
                c["percentage"] = round(c["percentage"] / total_pct * 100, 1)
        return dict(sorted(contributions.items(), key=lambda x: x[1]["percentage"], reverse=True))

    def counterfactual(self, current_data: pd.DataFrame, intervention: dict[str, float]) -> dict[str, Any]:
        if self.graph is None:
            return {"error": "No causal graph available"}
        cf_data = current_data.copy()
        for var, val in intervention.items():
            if var in cf_data.columns:
                cf_data[var] = val
        aqi_cols = [c for c in cf_data.columns if "aqi" in c.lower() or "pm" in c.lower()]
        if not aqi_cols:
            return {"error": "No AQI column found"}
        target = aqi_cols[0]
        predicted_aqi = 0
        for source in self.node_names:
            if source in self._causal_effects and source in intervention:
                effect = self._causal_effects[source]
                predicted_aqi += effect * intervention[source]
        current_aqi = float(current_data[target].iloc[0]) if hasattr(current_data, 'iloc') else float(current_data[target])
        return {
            "current_aqi": current_aqi,
            "counterfactual_aqi": abs(predicted_aqi),
            "intervention": intervention,
            "delta_aqi": current_aqi - abs(predicted_aqi),
        }

    def get_causal_effects(self) -> dict[str, float]:
        return self._causal_effects.copy()

    def get_node_names(self) -> list[str]:
        return list(self.node_names)

    def _fallback_attribution(self, data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        contributions: dict[str, dict[str, Any]] = {}
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != "aqi" and "pm" not in col.lower():
                contributions[col] = {
                    "source_type": col,
                    "percentage": round(100.0 / max(len(numeric_cols) - 1, 1), 1),
                    "confidence": 0.3,
                    "note": "correlation-based fallback",
                }
        return dict(sorted(contributions.items(), key=lambda x: x[1]["percentage"], reverse=True))
