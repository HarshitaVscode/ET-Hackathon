"""
Source Attribution Agent — Entry Point.

Attributing AQI to specific pollution sources using causal inference.
Answers queries like "What caused this pollution?" and supports
counterfactual "what if" simulations for policy planning.
"""

from __future__ import annotations

import io
from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI

from src.config import attribution_config
from src.causal_dag import CausalDAGLearner
from src.counterfactual import CounterfactualEngine

logger = __import__("structlog").get_logger(__name__)

_dag_learner: CausalDAGLearner | None = None
_counterfactual: CounterfactualEngine | None = None


def _generate_training_data() -> pd.DataFrame:
    """Generate synthetic training data for the causal DAG.

    In production, this comes from historical CAAQMS + satellite data.
    """
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

    # AQI as a causal function of sources + noise
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
    data["aqi"] = data["pm2_5"] * 2.0  # Simplified AQI conversion

    return data


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _dag_learner, _counterfactual

    logger.info("Training causal DAG")
    training_data = _generate_training_data()

    _dag_learner = CausalDAGLearner()
    dag = _dag_learner.learn_structure(training_data)

    _counterfactual = CounterfactualEngine(_dag_learner._causal_effects)

    logger.info(
        "Causal DAG trained",
        nodes=len(dag.nodes),
        edges=len(dag.edges),
        effects=len(_dag_learner._causal_effects),
    )
    yield


app = FastAPI(
    title="Vayu-Drishti Source Attribution Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "dag_ready": _dag_learner is not None and _dag_learner.graph is not None,
        "num_causal_effects": len(_dag_learner._causal_effects) if _dag_learner else 0,
    }


@app.post("/api/v1/process")
async def process_request(request: dict[str, Any]) -> dict[str, Any]:
    """Attribute pollution sources from current data."""
    if not _dag_learner:
        return {"error": "DAG not trained", "is_fallback": True}

    try:
        message = request.get("message", {})
        payload = message.get("payload", request)
        input_data = payload.get("input", payload)

        # Convert to DataFrame
        df = pd.DataFrame([input_data]) if isinstance(input_data, dict) else pd.DataFrame(input_data)

        # Ensure we have training columns
        for col in _dag_learner.node_names:
            if col not in df.columns:
                df[col] = 0.0

        # Run attribution
        contributions = _dag_learner.attribute_sources(df)

        return {
            "attribution": contributions,
            "total_sources": len(contributions),
            "top_source": max(contributions.items(), key=lambda x: x[1]["percentage"])[0] if contributions else None,
            "model": "causal_dag_pc_algorithm",
            "confidence": 0.85,
        }

    except Exception as exc:
        logger.exception("Attribution failed")
        return {"error": str(exc), "is_fallback": True}


@app.post("/api/v1/counterfactual")
async def counterfactual_query(query: dict[str, Any]) -> dict[str, Any]:
    """Answer a 'what if' policy question."""
    if not _counterfactual or not _dag_learner:
        return {"error": "Counterfactual engine not ready", "is_fallback": True}

    try:
        policy_name = query.get("policy_name", "")
        parameters = query.get("parameters", {})

        # Create current data snapshot
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


def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=attribution_config.app_port,
        reload=attribution_config.app_debug,
    )


if __name__ == "__main__":
    main()
