from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel

from .pipeline import EnforcementPipeline
from .config import EnforcementConfig

router = APIRouter(prefix="/api/v1/enforcement", tags=["Enforcement Intelligence"])
pipeline = EnforcementPipeline()
cfg = EnforcementConfig()


class HotspotResponse(BaseModel):
    id: str
    lat: float
    lon: float
    location_name: str
    state: str
    dominant_pollutant: str
    severity_score: float
    severity_label: str
    aqi: Optional[float] = None


class AttributionResponse(BaseModel):
    hotspot_id: str
    most_probable_cause: str
    confidence: float
    probability_distribution: Dict[str, float]
    supporting_evidence: List[str]


class RecommendationResponse(BaseModel):
    hotspot_id: str
    location_name: str
    priority: int
    risk_score: float
    recommendation: str
    responsible_authority: str
    severity: str
    confidence: float


@router.get("/hotspots")
async def get_hotspots() -> List[Dict]:
    hotspots = pipeline.detector.scan_notable_locations()
    return [hs.to_dict() for hs in hotspots]


@router.get("/hotspots/{hotspot_id}")
async def get_hotspot_detail(hotspot_id: str) -> Dict:
    hotspots = pipeline.detector.scan_notable_locations()
    hs = next((h for h in hotspots if h.id == hotspot_id), None)
    if not hs:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    attr = pipeline.attributor.attribute(hs)
    exp = pipeline.explainer.explain(hs, attr)
    pop = pipeline.pollution.get_population_exposure(hs.lat, hs.lon)
    rec = pipeline.recommender.generate(hs, attr, pop["population"])
    return {
        "hotspot": hs.to_dict(),
        "attribution": attr.to_dict(),
        "explanation": exp.to_dict(),
        "recommendation": rec.to_dict(),
    }


@router.get("/attributions")
async def get_attributions() -> List[Dict]:
    hotspots = pipeline.detector.scan_notable_locations()
    return [pipeline.attributor.attribute(hs).to_dict() for hs in hotspots]


@router.get("/recommendations")
async def get_recommendations() -> List[Dict]:
    hotspots = pipeline.detector.scan_notable_locations()
    recommendations = []
    for hs in hotspots:
        attr = pipeline.attributor.attribute(hs)
        pop = pipeline.pollution.get_population_exposure(hs.lat, hs.lon)
        rec = pipeline.recommender.generate(hs, attr, pop["population"])
        recommendations.append(rec)
    prioritized = pipeline.prioritizer.prioritize(recommendations)
    return [r.to_dict() for r in prioritized]


@router.post("/run")
async def run_pipeline() -> Dict:
    results = pipeline.run()
    return {
        "status": "success",
        "total_hotspots": results["total_hotspots"],
        "recommendations": results["recommendations"],
    }
