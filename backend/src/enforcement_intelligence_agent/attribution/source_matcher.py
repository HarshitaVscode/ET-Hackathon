import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from ..config import EnforcementConfig
from ..data.sources import SourceRegistry
from ..detection.hotspot import HotspotResult

cfg = EnforcementConfig()


@dataclass
class AttributionResult:
    hotspot_id: str
    most_probable_cause: str
    confidence: float
    probability_distribution: Dict[str, float]
    top_features: List[str]
    supporting_evidence: List[str]
    nearest_sources: List[Dict]
    alternative_causes: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "hotspot_id": self.hotspot_id,
            "most_probable_cause": self.most_probable_cause,
            "confidence": round(self.confidence * 100, 1),
            "probability_distribution": {k: round(v * 100, 1) for k, v in
                                          sorted(self.probability_distribution.items(),
                                                 key=lambda x: x[1], reverse=True)},
            "top_features": self.top_features,
            "supporting_evidence": self.supporting_evidence,
            "nearest_sources": self.nearest_sources,
            "alternative_causes": {k: round(v * 100, 1) for k, v in
                                    sorted(self.alternative_causes.items(),
                                           key=lambda x: x[1], reverse=True)},
        }


class SourceAttributor:
    def __init__(self):
        self.source_registry = SourceRegistry()

    def attribute(self, hotspot: HotspotResult) -> AttributionResult:
        pollutants = hotspot.detected_pollutants
        fires = hotspot.fire_observations
        weather = hotspot.meteorological_conditions
        nearby_sources = self.source_registry.get_nearby_sources(hotspot.lat, hotspot.lon)

        scores = {}
        evidence = []
        feature_importances = {}

        for source in cfg.source_list:
            profile = cfg.source_profiles[source]
            score = 0.0
            reasons = []

            for marker in profile:
                if marker == "fire_power" and fires:
                    frp_vals = [f.get("frp", 0) for f in fires]
                    score += min(max(frp_vals) / 50, 1.0) * 0.3
                    if max(frp_vals) > 50:
                        reasons.append(f"Active fire detected (FRP={max(frp_vals):.1f} MW)")
                elif marker in pollutants:
                    threshold = cfg.hotspot_pollutant_thresholds.get(marker, 1)
                    ratio = pollutants[marker] / threshold if threshold > 0 else 0
                    if ratio > 1:
                        contribution = min(ratio / 5, 1.0) * 0.25
                        score += contribution
                        reasons.append(f"Elevated {marker} ({(pollutants[marker]):.4f}, {ratio:.1f}x threshold)")

            nearby_of_type = [s for s in nearby_sources if s["type"] == source]
            if nearby_of_type:
                score += min(len(nearby_of_type) * 0.1, 0.3)
                min_dist = min(s["distance_km"] for s in nearby_of_type)
                score += max(0, 0.1 - min_dist / 500)
                reasons.append(f"{len(nearby_of_type)} nearby {source.replace('_', ' ')} sources (min dist: {min_dist:.1f}km)")

            if source == "dust_storm" and weather.get("wind_speed_kmh", 0) > 20:
                score += 0.2
                reasons.append(f"High wind speed ({weather['wind_speed_kmh']:.1f} km/h)")

            if source == "forest_fire" and fires:
                score += 0.15
                reasons.append(f"NASA FIRMS detection active")

            if source == "crop_burning":
                if pollutants.get("HCHO", 0) > cfg.hotspot_pollutant_thresholds.get("HCHO", 0.0003):
                    score += 0.15
                    reasons.append("HCHO signature consistent with biomass burning")
                if pollutants.get("CO", 0) > cfg.hotspot_pollutant_thresholds.get("CO", 0.05):
                    score += 0.1
                    reasons.append("CO enhancement from incomplete combustion")

            scores[source] = min(score, 1.0)
            if reasons:
                evidence.extend(reasons[:3])

            feature_importances[source] = score

        if not scores:
            scores["unknown"] = 0.5
            evidence.append("No clear source signature detected")

        total = sum(scores.values()) or 1
        probs = {k: v / total for k, v in scores.items()}

        best_source = max(probs, key=probs.get)
        best_conf = probs[best_source]

        alternatives = {k: v for k, v in probs.items() if k != best_source}
        top_features = sorted(feature_importances, key=feature_importances.get, reverse=True)[:5]

        return AttributionResult(
            hotspot_id=hotspot.id,
            most_probable_cause=best_source,
            confidence=best_conf,
            probability_distribution=probs,
            top_features=top_features,
            supporting_evidence=list(set(evidence))[:10],
            nearest_sources=nearby_sources[:5],
            alternative_causes=alternatives,
        )
