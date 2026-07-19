from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.agents.source_attribution.causal_dag import CausalDAGLearner
from src.agents.source_attribution.counterfactual import CounterfactualEngine
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)

_dag_learner: CausalDAGLearner | None = None
_counterfactual: CounterfactualEngine | None = None


def _generate_training_data() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    n = 1000
    data = pd.DataFrame({
        "traffic_emission": rng.exponential(50, n),
        "industry_emission": rng.exponential(30, n),
        "construction_dust": rng.exponential(20, n),
        "agricultural_burning": rng.exponential(15, n),
        "waste_burning": rng.exponential(10, n),
        "wind_speed": rng.uniform(0, 10, n),
        "pbl_height": rng.uniform(200, 2000, n),
        "temperature": rng.normal(30, 5, n),
    })
    pm25 = (
        0.4 * data["traffic_emission"]
        + 0.3 * data["industry_emission"]
        + 0.15 * data["construction_dust"]
        + 0.4 * data["agricultural_burning"]
        + 0.2 * data["waste_burning"]
        - 3.0 * data["wind_speed"]
        - 0.02 * data["pbl_height"]
        + rng.normal(0, 10, n)
    )
    data["pm2_5"] = np.maximum(0, pm25)
    data["aqi"] = data["pm2_5"] * 2.0
    return data


def initialize():
    global _dag_learner, _counterfactual
    logger.info("Training causal DAG")
    training_data = _generate_training_data()
    _dag_learner = CausalDAGLearner()
    dag = _dag_learner.learn_structure(training_data)
    _counterfactual = CounterfactualEngine(_dag_learner.get_causal_effects())
    logger.info(
        "Causal DAG trained",
        nodes=len(dag.nodes),
        edges=len(dag.edges),
        effects=len(_dag_learner.get_causal_effects()),
    )


async def process_request(request: dict[str, Any]) -> dict[str, Any]:
    if not _dag_learner:
        return {"error": "DAG not trained", "is_fallback": True}
    try:
        message = request.get("message", request)
        payload = message.get("payload", request)
        input_data = payload.get("input", payload)
        df = pd.DataFrame([input_data]) if isinstance(input_data, dict) else pd.DataFrame(input_data)
        for col in _dag_learner.get_node_names():
            if col not in df.columns:
                df[col] = 0.0
        contributions = _dag_learner.attribute_sources(df)
        return {
            "attribution": contributions,
            "total_sources": len(contributions),
            "top_source": max(contributions.items(), key=lambda x: x[1]["percentage"])[0] if contributions else None,
            "top_source_percentage": max(c["percentage"] for c in contributions.values()) if contributions else 0.0,
            "model": "causal_dag_pc_algorithm",
            "confidence": 0.85,
        }
    except Exception as exc:
        logger.exception("Attribution failed")
        return {"error": str(exc), "is_fallback": True}


async def counterfactual_query(query: dict[str, Any]) -> dict[str, Any]:
    if not _counterfactual or not _dag_learner:
        return {"error": "Counterfactual engine not ready", "is_fallback": True}
    try:
        policy_name = query.get("policy_name", "")
        parameters = query.get("parameters", {})
        current_data = pd.DataFrame([{
            "traffic_emission": parameters.get("traffic_emission", 50),
            "industry_emission": parameters.get("industry_emission", 30),
            "construction_dust": parameters.get("construction_dust", 20),
            "agricultural_burning": parameters.get("agricultural_burning", 15),
            "waste_burning": parameters.get("waste_burning", 10),
            "wind_speed": parameters.get("wind_speed", 3.5),
            "pbl_height": parameters.get("pbl_height", 1000),
            "temperature": parameters.get("temperature", 30),
        }])
        result = _counterfactual.simulate_policy(
            current_data=current_data,
            policy_name=policy_name,
            parameters=parameters,
        )
        return result
    except Exception as exc:
        logger.exception("Counterfactual query failed")
        return {"error": str(exc), "is_fallback": True}
