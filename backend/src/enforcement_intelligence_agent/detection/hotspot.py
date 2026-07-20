import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from ..config import EnforcementConfig
from ..data.satellite import SatelliteDataFetcher
from ..data.fire import FireDataFetcher
from ..data.pollution import PollutionDataFetcher
from ..data.meteorology import MeteorologyDataFetcher

cfg = EnforcementConfig()


@dataclass
class HotspotResult:
    id: str
    lat: float
    lon: float
    location_name: str
    state: str
    district: str = ""
    dominant_pollutant: str = ""
    severity_score: float = 0.0
    severity_label: str = "Low"
    detected_pollutants: Dict[str, float] = field(default_factory=dict)
    satellite_observations: Dict[str, float] = field(default_factory=dict)
    meteorological_conditions: Dict[str, float] = field(default_factory=dict)
    fire_observations: List[Dict] = field(default_factory=list)
    aqi_data: Dict = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "lat": self.lat,
            "lon": self.lon,
            "location_name": self.location_name,
            "state": self.state,
            "district": self.district,
            "dominant_pollutant": self.dominant_pollutant,
            "severity_score": round(self.severity_score, 2),
            "severity_label": self.severity_label,
            "detected_pollutants": {k: round(v, 4) for k, v in self.detected_pollutants.items()},
            "satellite_observations": {k: round(v, 4) for k, v in self.satellite_observations.items()},
            "meteorological_conditions": {k: round(v, 1) for k, v in self.meteorological_conditions.items()},
            "fire_observations": self.fire_observations,
            "aqi_data": self.aqi_data,
            "timestamp": self.timestamp,
        }


class HotspotDetector:
    def __init__(self):
        self.satellite = SatelliteDataFetcher()
        self.fire = FireDataFetcher()
        self.pollution = PollutionDataFetcher()
        self.weather = MeteorologyDataFetcher()

    def scan_location(self, lat: float, lon: float, location_name: str = "") -> Optional[HotspotResult]:
        sat_data = self.satellite.get_all_species(lat, lon)
        fire_data = self.fire.get_thermal_anomalies(lat, lon)
        aqi = self.pollution.get_location_aqi(lat, lon)
        weather = self.weather.fetch_weather(lat, lon)

        if any(v is None for v in sat_data.values()):
            return None

        pollutant_values = {k: v for k, v in sat_data.items() if v is not None}
        if aqi.get("pm25"):
            pollutant_values["PM25"] = aqi["pm25"]

        dominant = max(pollutant_values, key=lambda k: abs(pollutant_values[k]) / cfg.hotspot_pollutant_thresholds.get(k, 1))
        severity = self._compute_severity(pollutant_values, aqi, fire_data, weather)

        from ..data.geo_utils import GeoUtils
        state = GeoUtils.get_state_from_coords(lat, lon)

        result = HotspotResult(
            id=f"HS-{lat:.2f}-{lon:.2f}".replace(".", "_"),
            lat=lat,
            lon=lon,
            location_name=location_name or GeoUtils.get_state_from_coords(lat, lon),
            state=state,
            dominant_pollutant=dominant,
            severity_score=severity,
            severity_label=self._severity_label(severity),
            detected_pollutants=pollutant_values,
            satellite_observations=sat_data,
            meteorological_conditions=weather,
            fire_observations=fire_data,
            aqi_data=aqi,
            timestamp=datetime.now().isoformat(),
        )
        return result

    def scan_notable_locations(self) -> List[HotspotResult]:
        results = []
        for loc in self.satellite.get_notable_locations():
            hs = self.scan_location(loc["lat"], loc["lon"], loc["name"])
            if hs:
                hs.state = loc.get("state", hs.state)
                results.append(hs)
        return results

    def scan_grid(self, bounds: Tuple[float, float, float, float],
                  resolution: float = 0.5) -> List[HotspotResult]:
        min_lat, min_lon, max_lat, max_lon = bounds
        results = []
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                hs = self.scan_location(lat, lon, f"Grid-{lat:.1f}-{lon:.1f}")
                if hs and hs.severity_score > cfg.confidence_threshold:
                    results.append(hs)
                lon += resolution
            lat += resolution
        return results

    def _compute_severity(self, pollutants: Dict, aqi: Dict,
                          fires: List, weather: Dict) -> float:
        score = 0.0
        for pollutant, value in pollutants.items():
            threshold = cfg.hotspot_pollutant_thresholds.get(pollutant, 1)
            if threshold > 0:
                score += (value / threshold) * 10
        if aqi.get("aqi"):
            score += (aqi["aqi"] / 500) * 20
        if fires:
            score += min(len(fires) * 5, 15)
            max_frp = max(f.get("frp", 0) for f in fires)
            score += (max_frp / 100) * 10
        if weather.get("wind_speed_kmh", 10) < 5:
            score += 5
        if self.weather.is_inversion_likely(weather):
            score += 5
        return min(score / 100, 1.0)

    @staticmethod
    def _severity_label(score: float) -> str:
        if score >= 0.8: return "Very High"
        if score >= 0.6: return "High"
        if score >= 0.35: return "Moderate"
        return "Low"
