from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class CounterfactualEngine:
    def __init__(self, causal_effects: dict[str, float]) -> None:
        self.causal_effects = causal_effects

    def simulate_policy(
        self,
        current_data: pd.DataFrame,
        policy_name: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        interventions = self._get_policy_intervention(policy_name, parameters)
        cf_data = current_data.copy()
        for var, val in interventions.items():
            if var in cf_data.columns:
                cf_data[var] = val

        current_aqi = float(current_data.get("aqi", current_data.get("pm2_5", [200]).iloc[0]))
        predicted_aqi = self._estimate_aqi(cf_data)

        policy_effects = self._compute_policy_effects(cf_data, current_data)

        return {
            "policy_name": policy_name,
            "current_aqi": current_aqi,
            "predicted_aqi": predicted_aqi,
            "reduction_percent": round((current_aqi - predicted_aqi) / current_aqi * 100, 1) if current_aqi > 0 else 0,
            "confidence": 0.75,
            "estimated_health_savings_cr": round((current_aqi - predicted_aqi) * 0.05, 1),
            "interventions_applied": interventions,
            "effects_by_source": policy_effects,
        }

    def _get_policy_intervention(self, policy_name: str, parameters: dict[str, Any]) -> dict[str, float]:
        policies = {
            "road_closure": {"traffic_emission": 20},
            "industry_reduction": {"industry_emission": 10},
            "burning_reduction": {"agricultural_burning": 5, "waste_burning": 3},
            "ev_adoption": {"traffic_emission": 15},
            "construction_ban": {"construction_dust": 5},
            "green_buffer": {"construction_dust": 3, "traffic_emission": 5},
        }
        base = policies.get(policy_name, {})
        return {**base, **parameters}

    def _estimate_aqi(self, data: pd.DataFrame) -> float:
        aqi = 200
        for source, effect in self.causal_effects.items():
            if source in data.columns:
                aqi += effect * float(data[source].iloc[0])
        return max(0, aqi)

    def _compute_policy_effects(self, cf_data: pd.DataFrame, current_data: pd.DataFrame) -> list[dict[str, Any]]:
        effects = []
        for source, effect in self.causal_effects.items():
            if source in cf_data.columns and source in current_data.columns:
                old_val = float(current_data[source].iloc[0]) if hasattr(current_data, 'iloc') else float(current_data[source])
                new_val = float(cf_data[source].iloc[0]) if hasattr(cf_data, 'iloc') else float(cf_data[source])
                delta = effect * (new_val - old_val)
                effects.append({
                    "source": source,
                    "reduction": round(old_val - new_val, 1),
                    "aqi_impact": round(delta, 1),
                })
        return effects
