from typing import List, Dict
from dataclasses import dataclass, field

from ..config import EnforcementConfig
from ..detection.hotspot import HotspotResult
from ..attribution.source_matcher import AttributionResult

cfg = EnforcementConfig()


@dataclass
class EnforcementRecommendation:
    hotspot_id: str
    location_name: str
    priority: int
    risk_score: float
    recommendation: str
    responsible_authority: str
    action_type: str
    severity: str
    confidence: float
    population_exposed: int

    def to_dict(self) -> Dict:
        return {
            "hotspot_id": self.hotspot_id,
            "location_name": self.location_name,
            "priority": self.priority,
            "risk_score": round(self.risk_score, 2),
            "recommendation": self.recommendation,
            "responsible_authority": self.responsible_authority,
            "action_type": self.action_type,
            "severity": self.severity,
            "confidence": round(self.confidence * 100, 1),
            "population_exposed": self.population_exposed,
        }


class EnforcementRecommender:
    def generate(self, hotspot: HotspotResult, attribution: AttributionResult,
                 population: int) -> EnforcementRecommendation:
        source = attribution.most_probable_cause
        severity = hotspot.severity_label

        recommendation = cfg.get_recommendation_for_source(source, severity)
        authority = cfg.get_authority_for_source(source)

        action_map = {
            "forest_fire": "immediate_response",
            "crop_burning": "enforcement_action",
            "industrial": "inspection",
            "construction": "inspection",
            "waste_burning": "enforcement_action",
            "brick_kiln": "inspection",
            "power_plant": "inspection",
            "diesel_traffic": "traffic_management",
            "urban_congestion": "traffic_management",
            "mining": "inspection",
            "dust_storm": "public_health_advisory",
        }
        action_type = action_map.get(source, "investigation")

        risk_score = (
            hotspot.severity_score * 0.3 +
            attribution.confidence * 0.25 +
            min(population / 10_000_000, 1.0) * 0.25 +
            0.2
        )

        return EnforcementRecommendation(
            hotspot_id=hotspot.id,
            location_name=hotspot.location_name,
            priority=0,
            risk_score=risk_score,
            recommendation=recommendation,
            responsible_authority=authority,
            action_type=action_type,
            severity=severity,
            confidence=attribution.confidence,
            population_exposed=population,
        )
