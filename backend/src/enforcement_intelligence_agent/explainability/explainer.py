import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..detection.hotspot import HotspotResult
from ..attribution.source_matcher import AttributionResult


@dataclass
class ExplanationResult:
    most_probable_cause: str
    confidence: float
    reasoning_tree: List[str]
    top_influential_features: List[Dict]
    satellite_evidence: List[str]
    meteorological_evidence: List[str]
    historical_context: List[str]
    temporal_context: str
    spatial_context: str
    shap_explanation: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "most_probable_cause": self.most_probable_cause.replace("_", " ").title(),
            "confidence": f"{self.confidence:.1%}",
            "reasoning_tree": self.reasoning_tree,
            "top_influential_features": self.top_influential_features,
            "satellite_evidence": self.satellite_evidence,
            "meteorological_evidence": self.meteorological_evidence,
            "historical_context": self.historical_context,
            "temporal_context": self.temporal_context,
            "spatial_context": self.spatial_context,
        }


class ExplainableAI:
    def explain(self, hotspot: HotspotResult, attribution: AttributionResult) -> ExplanationResult:
        reasoning = []
        sat_ev = []
        met_ev = []
        hist = []
        features = []

        reasoning.append(f"Step 1: Detected pollution hotspot at {hotspot.location_name} "
                         f"({hotspot.lat:.2f}, {hotspot.lon:.2f})")
        reasoning.append(f"Step 2: Dominant pollutant identified as {hotspot.dominant_pollutant} "
                         f"(severity: {hotspot.severity_label})")

        for pol, val in sorted(hotspot.detected_pollutants.items(),
                                key=lambda x: abs(x[1]), reverse=True)[:5]:
            features.append({
                "feature": pol,
                "value": round(val, 4),
                "importance": round(abs(val) / sum(abs(v) for v in hotspot.detected_pollutants.values()), 3)
            })

        reasoning.append(f"Step 3: Source attribution suggests {attribution.most_probable_cause.replace('_', ' ')} "
                         f"with {attribution.confidence:.1%} confidence")

        for ev in attribution.supporting_evidence[:3]:
            reasoning.append(f"  - {ev}")

        for pol, val in hotspot.satellite_observations.items():
            if val is not None:
                sat_ev.append(f"TROPOMI {pol}: {val:.4f} mol/m²")

        if hotspot.fire_observations:
            for fire in hotspot.fire_observations[:3]:
                sat_ev.append(f"NASA FIRMS fire: FRP={fire.get('frp', 0):.1f} MW, "
                              f"confidence={fire.get('confidence', 0)}% ({fire.get('satellite', 'N/A')})")

        met = hotspot.meteorological_conditions
        met_ev.append(f"Temperature: {met.get('temperature_c', 'N/A')}°C")
        met_ev.append(f"Humidity: {met.get('humidity_pct', 'N/A')}%")
        met_ev.append(f"Wind: {met.get('wind_speed_kmh', 'N/A')} km/h "
                       f"from {MeteorologyHelper.get_wind_direction_name(met.get('wind_direction_deg', 0))}")
        met_ev.append(f"Visibility: {met.get('visibility_km', 'N/A')} km")
        met_ev.append(f"Boundary Layer: {met.get('boundary_layer_height_m', 'N/A')} m")

        hist.append(f"Current AQI: {hotspot.aqi_data.get('aqi', 'N/A')} "
                     f"({hotspot.aqi_data.get('category', 'N/A')})")
        hist.append(f"Dominant pollutant in satellite data: {hotspot.dominant_pollutant}")

        temporal = f"Detected at {hotspot.timestamp}"
        spatial = f"Location: {hotspot.location_name}, {hotspot.state} ({hotspot.lat:.4f}°N, {hotspot.lon:.4f}°E)"

        return ExplanationResult(
            most_probable_cause=attribution.most_probable_cause,
            confidence=attribution.confidence,
            reasoning_tree=reasoning,
            top_influential_features=features,
            satellite_evidence=sat_ev,
            meteorological_evidence=met_ev,
            historical_context=hist,
            temporal_context=temporal,
            spatial_context=spatial,
        )


class MeteorologyHelper:
    @staticmethod
    def get_wind_direction_name(deg: float) -> str:
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        return dirs[round(deg / 22.5) % 16]
