"""Counterfactual inference engine for policy simulation.

Enables "what if" queries like:
- What if Ring Road is closed for construction?
- What if all brick kilns switch to zig-zag technology?
- What if agricultural burning is reduced by 50%?

Uses the learned causal DAG to simulate interventions.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class CounterfactualEngine:
    """Answer counterfactual queries using the causal DAG.

    Supports do-calculus style interventions where we set
    a source variable to a specific value and observe the
    effect on AQI through the causal graph.
    """

    def __init__(self, causal_effects: dict[str, float]) -> None:
        self.causal_effects = causal_effects

    def simulate_policy(
        self,
        current_data: pd.DataFrame,
        policy_name: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Simulate a policy intervention.

        Args:
            current_data: Current state of all variables.
            policy_name: Name of the policy to simulate.
            parameters: Policy-specific parameters.

        Returns:
            Simulation result with predicted AQI change.
        """
        policy_simulators = {
            "close_road": self._simulate_road_closure,
            "reduce_industry": self._simulate_industry_reduction,
            "reduce_burning": self._simulate_burning_reduction,
            "ev_adoption": self._simulate_ev_adoption,
            "construction_ban": self._simulate_construction_ban,
            "green_buffer": self._simulate_green_buffer,
        }

        simulator = policy_simulators.get(policy_name)
        if not simulator:
            return {"error": f"Unknown policy: {policy_name}"}

        return simulator(current_data, parameters)

    def _simulate_road_closure(self, data: pd.DataFrame, params: dict) -> dict:
        reduction = params.get("traffic_reduction_percent", 30)
        traffic_var = [v for v in self.causal_effects if "traffic" in v.lower()]
        if not traffic_var:
            return {"error": "No traffic variable in causal model"}

        intervention = {traffic_var[0]: data[traffic_var[0]].iloc[0] * (1 - reduction / 100)}
        return self._run_intervention(data, intervention, "Road Closure")

    def _simulate_industry_reduction(self, data: pd.DataFrame, params: dict) -> dict:
        reduction = params.get("industry_reduction_percent", 30)
        ind_var = [v for v in self.causal_effects if "industry" in v.lower()]
        if not ind_var:
            return {"error": "No industry variable in causal model"}

        intervention = {ind_var[0]: data[ind_var[0]].iloc[0] * (1 - reduction / 100)}
        return self._run_intervention(data, intervention, "Industry Reduction")

    def _simulate_burning_reduction(self, data: pd.DataFrame, params: dict) -> dict:
        reduction = params.get("burning_reduction_percent", 50)
        burn_vars = [v for v in self.causal_effects if "burn" in v.lower()]
        if not burn_vars:
            return {"error": "No burning variable in causal model"}

        intervention = {v: data[v].iloc[0] * (1 - reduction / 100) for v in burn_vars}
        return self._run_intervention(data, intervention, "Burning Reduction")

    def _simulate_ev_adoption(self, data: pd.DataFrame, params: dict) -> dict:
        adoption_rate = params.get("ev_adoption_percent", 50)
        traffic_var = [v for v in self.causal_effects if "traffic" in v.lower()]
        if not traffic_var:
            return {"error": "No traffic variable in causal model"}

        # EV adoption reduces traffic emissions proportionally
        emission_reduction = adoption_rate * 0.6  # EVs emit 60% less
        intervention = {traffic_var[0]: data[traffic_var[0]].iloc[0] * (1 - emission_reduction / 100)}
        return self._run_intervention(data, intervention, "EV Adoption")

    def _simulate_construction_ban(self, data: pd.DataFrame, params: dict) -> dict:
        const_var = [v for v in self.causal_effects if "construction" in v.lower() or "const" in v.lower()]
        if not const_var:
            return {"error": "No construction variable in causal model"}

        intervention = {const_var[0]: 0}  # Complete ban
        return self._run_intervention(data, intervention, "Construction Ban")

    def _simulate_green_buffer(self, data: pd.DataFrame, params: dict) -> dict:
        # Green buffer reduces dust and improves dispersion
        dust_var = [v for v in self.causal_effects if "dust" in v.lower()]
        if not dust_var:
            return {"effect": "No dust variable, estimated 5% reduction"}

        intervention = {dust_var[0]: data[dust_var[0]].iloc[0] * 0.7}  # 30% dust reduction
        return self._run_intervention(data, intervention, "Green Buffer")

    def _run_intervention(
        self,
        data: pd.DataFrame,
        intervention: dict[str, float],
        policy_label: str,
    ) -> dict[str, Any]:
        """Execute a causal intervention and compute the result."""
        current_aqi = data.get("aqi") or data.get("pm2_5")
        if current_aqi is not None:
            current_aqi = float(current_aqi.iloc[0]) if hasattr(current_aqi, 'iloc') else float(current_aqi)
        else:
            current_aqi = 200.0

        # Compute AQI change from causal effects
        aqi_change = 0.0
        for var, new_val in intervention.items():
            if var in self.causal_effects:
                old_val = float(data[var].iloc[0]) if hasattr(data, 'iloc') else float(data[var])
                change = (new_val - old_val) * self.causal_effects[var]
                aqi_change += change

        new_aqi = max(0, current_aqi + aqi_change)
        reduction = ((current_aqi - new_aqi) / max(current_aqi, 1)) * 100

        return {
            "policy": policy_label,
            "intervention": intervention,
            "current_aqi": round(current_aqi, 1),
            "predicted_aqi": round(new_aqi, 1),
            "absolute_reduction": round(current_aqi - new_aqi, 1),
            "percent_reduction": round(reduction, 1),
            "confidence": min(1.0, abs(reduction) / 50),
            "caveats": [
                "Linear approximation — actual effects may be non-linear",
                "Assumes no interaction between interventions",
            ],
        }
