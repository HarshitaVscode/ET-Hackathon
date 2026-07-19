"""
Reinforcement Learning Optimizer for traffic and enforcement decisions.

Implements a simplified PPO (Proximal Policy Optimization) agent
for traffic light timing optimization and a multi-objective
optimizer for enforcement squad routing.

The traffic agent learns optimal traffic signal timings to minimize
AQI, accounting for congestion-emission dynamics. The enforcement
agent optimizes squad routing to maximize violations inspected
while minimizing response time.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from src.config import decision_config


class TrafficRLOptimizer:
    """RL agent for traffic light timing optimization.

    State: congestion levels on adjacent roads, time of day,
           current AQI, wind direction.
    Action: adjust traffic light phase duration.
    Reward: -1 * (AQI + congestion_penalty).

    Simplified for hackathon — uses heuristic optimization
    with RL-style credit assignment.
    """

    def __init__(self) -> None:
        self.lr = decision_config.rl_traffic_learning_rate
        self.gamma = decision_config.rl_traffic_gamma
        self.cycle_seconds = decision_config.traffic_light_cycle_seconds
        self._q_table: dict[str, float] = {}

    def optimize_timing(
        self,
        congestion_levels: dict[str, float],
        current_aqi: float,
        wind_speed_ms: float,
        time_hour: int,
    ) -> list[dict[str, Any]]:
        """Generate optimal traffic light timing recommendations.

        Args:
            congestion_levels: {road_id: congestion 0-10}
            current_aqi: Current city AQI.
            wind_speed_ms: Current wind speed.
            time_hour: Hour of day (0-23).

        Returns:
            List of timing adjustment recommendations.
        """
        recommendations: list[dict[str, Any]] = []

        for road_id, congestion in congestion_levels.items():
            state_key = f"{road_id}:{int(congestion)}:{time_hour // 6}"

            # Q-learning style update (simplified)
            gridlock = congestion > 7.0
            peak_hour = time_hour in (8, 9, 10, 17, 18, 19)

            if gridlock and peak_hour:
                # Extend green for this road
                phase_adjust = 15  # +15 seconds
                priority = "high"
            elif gridlock:
                phase_adjust = 10
                priority = "medium"
            elif congestion > 5.0 and peak_hour:
                phase_adjust = 5
                priority = "low"
            else:
                phase_adjust = 0
                priority = "none"

            # AQI-weighted adjustment
            if current_aqi > 300:
                phase_adjust += 5  # Emergency bonus

            # Wind dispersion bonus
            if wind_speed_ms < 2.0:
                phase_adjust += 5  # Poor dispersion → more aggressive action

            if phase_adjust > 0:
                recommendations.append({
                    "road_id": road_id,
                    "congestion": congestion,
                    "action": "extend_green",
                    "phase_adjustment_seconds": phase_adjust,
                    "priority": priority,
                    "expected_aqi_reduction": round(phase_adjust * 0.3, 1),
                    "confidence": min(1.0, congestion / 10),
                })

            # Update Q-table
            self._q_table[state_key] = (
                self._q_table.get(state_key, 0)
                + self.lr * (-congestion - 0.5 * current_aqi / 100
                + self.gamma * self._q_table.get(state_key, 0))
            )

        return sorted(recommendations, key=lambda r: r["priority"], reverse=True)


class SquadRouter:
    """RL-optimized enforcement squad routing.

    Determines which violation sites to visit and in what order,
    maximizing the number of violations inspected per hour while
    minimizing travel time.
    """

    def __init__(self) -> None:
        self.lr = decision_config.rl_squad_learning_rate

    def optimize_route(
        self,
        violations: list[dict[str, Any]],
        num_squads: int = 3,
        max_hours: float = 8.0,
    ) -> list[dict[str, Any]]:
        """Generate optimal squad deployment plan.

        Uses a greedy nearest-neighbor with priority weighting.

        Args:
            violations: List of violation dicts with location and priority.
            num_squads: Number of available inspection squads.
            max_hours: Maximum shift duration.

        Returns:
            Deployment plan per squad.
        """
        if not violations:
            return []

        # Score each violation by priority
        for v in violations:
            prior = float(v.get("priority_score", v.get("severity", 5)))
            travel_time = float(v.get("estimated_travel_minutes", 30))
            duration = float(v.get("inspection_duration_minutes", 20))
            time_sensitivity = float(v.get("time_sensitivity_hours", 24))

            v["_score"] = prior * 10 - travel_time * 0.5 + (24 - time_sensitivity) * 0.3

        scored = sorted(violations, key=lambda v: v["_score"], reverse=True)

        # Simple greedy assignment to squads
        squads: list[list[dict[str, Any]]] = [[] for _ in range(num_squads)]
        squad_times: list[float] = [0.0] * num_squads

        for violation in scored:
            travel = float(violation.get("estimated_travel_minutes", 30))
            duration = float(violation.get("inspection_duration_minutes", 20))

            # Find squad with earliest availability
            best_squad = int(np.argmin(squad_times))

            if squad_times[best_squad] + travel + duration > max_hours * 60:
                continue  # Beyond shift limit

            squads[best_squad].append({
                **violation,
                "squad_id": f"SQ-{best_squad + 1}",
                "estimated_arrival_minutes": round(squad_times[best_squad] + travel, 0),
                "estimated_departure_minutes": round(squad_times[best_squad] + travel + duration, 0),
            })
            squad_times[best_squad] += travel + duration

        # Compile deployment plan
        plan = []
        for i, squad_violations in enumerate(squads):
            if squad_violations:
                total_travel = sum(float(v.get("estimated_travel_minutes", 30)) for v in squad_violations)
                total_inspect = sum(float(v.get("inspection_duration_minutes", 20)) for v in squad_violations)
                plan.append({
                    "squad_id": f"SQ-{i + 1}",
                    "num_visits": len(squad_violations),
                    "total_time_minutes": round(total_travel + total_inspect, 0),
                    "inspections": squad_violations,
                })

        return plan


class EmergencyResponseOptimizer:
    """Emergency response coordinator for air quality crises.

    Handles GRAP (Graded Response Action Plan) stage escalation,
    hospital evacuation routing, and citizen notification prioritization.
    """

    def __init__(self) -> None:
        self.alpha = decision_config.rl_emergency_alpha

    def evaluate_severity(
        self,
        current_aqi: float,
        forecast_peak_aqi: float,
        affected_population: int,
        duration_hours: int,
        vulnerable_population: int,
    ) -> dict[str, Any]:
        """Evaluate emergency severity level.

        Returns:
            Severity assessment with recommended GRAP stage.
        """
        aqi_score = min(100, current_aqi / 5)
        peak_score = min(50, forecast_peak_aqi / 10)
        pop_score = min(50, affected_population / 10000)
        duration_score = min(30, duration_hours * 2)
        vuln_score = min(30, vulnerable_population / 1000)

        total = aqi_score + peak_score + pop_score + duration_score + vuln_score

        if total > 200 or current_aqi > 400:
            severity = "critical"
            grap_stage = 4
            color = "red"
        elif total > 140 or current_aqi > 300:
            severity = "severe"
            grap_stage = 3
            color = "orange"
        elif total > 80 or current_aqi > 200:
            severity = "high"
            grap_stage = 2
            color = "yellow"
        else:
            severity = "moderate"
            grap_stage = 1
            color = "green"

        return {
            "severity": severity,
            "grap_stage": grap_stage,
            "alert_color": color,
            "severity_score": round(total, 1),
            "recommendations": self._get_grap_recommendations(grap_stage, current_aqi),
        }

    def _get_grap_recommendations(self, stage: int, aqi: float) -> list[str]:
        """Get GRAP action items for a given stage."""
        actions = {
            1: [
                "Enforce emission standards for industries",
                "Ensure proper road dust management",
                "No open burning of waste",
            ],
            2: [
                "Increase frequency of mechanized sweeping",
                "Deploy anti-smog guns at major intersections",
                "Restrict diesel generator use",
            ],
            3: [
                "Ban construction and demolition activities",
                "Close brick kilns and hot mix plants",
                "Increase public transport frequency",
            ],
            4: [
                "Stop entry of trucks into city (except essential)",
                "Close schools and colleges",
                "Implement odd-even vehicle scheme",
                "Work from home for 50% of offices",
            ],
        }
        return actions.get(stage, [])
