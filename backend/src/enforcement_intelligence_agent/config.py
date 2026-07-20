from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

MODULE_DIR = Path(__file__).parent


@dataclass
class EnforcementConfig:
    module_dir: Path = MODULE_DIR
    artifacts_dir: Path = MODULE_DIR / "artifacts"
    geojson_dir: Path = MODULE_DIR / "artifacts" / "geojson"
    models_dir: Path = MODULE_DIR / "artifacts" / "models"
    viz_dir: Path = MODULE_DIR / "artifacts" / "visualizations"

    hotspot_pollutant_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "NO2": 0.0002,
        "CO": 0.05,
        "SO2": 0.0005,
        "HCHO": 0.0003,
        "aerosol_index": 1.0,
        "PM25": 60,
        "PM10": 100,
    })

    source_profiles: Dict[str, List[str]] = field(default_factory=lambda: {
        "forest_fire": ["CO", "HCHO", "aerosol_index", "fire_power"],
        "crop_burning": ["CO", "HCHO", "aerosol_index", "PM25"],
        "industrial": ["SO2", "NO2", "CO", "PM25"],
        "construction": ["PM10", "PM25"],
        "waste_burning": ["CO", "HCHO", "PM25"],
        "brick_kiln": ["SO2", "CO", "PM25"],
        "power_plant": ["SO2", "NO2", "CO"],
        "diesel_traffic": ["NO2", "CO", "PM25"],
        "urban_congestion": ["NO2", "CO"],
        "mining": ["PM10", "aerosol_index"],
        "dust_storm": ["PM10", "aerosol_index"],
    })

    confidence_threshold: float = 0.5
    risk_weights: Dict[str, float] = field(default_factory=lambda: {
        "pollution_intensity": 0.25,
        "population_exposure": 0.20,
        "forecast_impact": 0.15,
        "source_severity": 0.20,
        "confidence": 0.10,
        "temporal_urgency": 0.10,
    })

    india_bounds: Dict[str, float] = field(default_factory=lambda: {
        "min_lat": 6.5, "max_lat": 37.0,
        "min_lon": 68.0, "max_lon": 97.5,
    })

    openaq_api_url: str = "https://api.openaq.org/v3"
    firms_api_url: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    sentinel_hub_url: str = "https://services.sentinel-hub.com/ogc/wms"

    cache_ttl_hours: int = 6
    max_hotspots: int = 50
    cluster_radius_km: float = 10.0

    @property
    def source_list(self) -> List[str]:
        return list(self.source_profiles.keys())

    def get_authority_for_source(self, source: str) -> str:
        authority_map = {
            "forest_fire": "Forest Department / ISRO",
            "crop_burning": "State Pollution Control Board / Agriculture Dept",
            "industrial": "State Pollution Control Board / CPCB",
            "construction": "Municipal Corporation / Town Planning",
            "waste_burning": "Municipal Corporation / Health Department",
            "brick_kiln": "State Pollution Control Board / Labour Dept",
            "power_plant": "Central Electricity Authority / CPCB",
            "diesel_traffic": "Traffic Police / Transport Department",
            "urban_congestion": "Traffic Police / Urban Development",
            "mining": "Ministry of Mines / State Pollution Control Board",
            "dust_storm": "Disaster Management Authority / IMD",
        }
        return authority_map.get(source, "State Pollution Control Board")

    def get_recommendation_for_source(self, source: str, severity: str = "high") -> str:
        recs = {
            "forest_fire": "Deploy Fire Management Team; Issue Red Alert; Evacuate if needed",
            "crop_burning": "Issue Crop Burning Notice; Deploy enforcement squad; Impose fine",
            "industrial": "Inspect Industrial Facility; Check emission compliance; Issue shutdown notice if violated",
            "construction": "Conduct Construction Site Inspection; Verify dust mitigation measures",
            "waste_burning": "Inspect Waste Burning Area; Issue penalty; Deploy mobile vigilance unit",
            "brick_kiln": "Inspect Brick Kiln cluster; Verify zig-zag technology compliance",
            "power_plant": "Inspect Power Plant emissions; Verify FGD installation; Check compliance report",
            "diesel_traffic": "Increase Traffic Restrictions; Deploy alternate route plan; Strengthen PUC checks",
            "urban_congestion": "Implement Odd-Even scheme; Deploy traffic management; Promote public transport",
            "mining": "Inspect Mining Site; Verify environmental clearance; Check dust suppression measures",
            "dust_storm": "Issue Public Health Advisory; Deploy medical camps; Distribute masks",
        }
        return recs.get(source, "Deploy Mobile Air Quality Unit for further investigation")
