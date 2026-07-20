from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from .config import EnforcementConfig
from .detection.hotspot import HotspotDetector, HotspotResult
from .attribution.source_matcher import SourceAttributor, AttributionResult
from .explainability.explainer import ExplainableAI, ExplanationResult
from .enforcement.recommender import EnforcementRecommender, EnforcementRecommendation
from .enforcement.prioritizer import HotspotPrioritizer
from .visualization.plots import EnforcementPlots
from .visualization.map_generator import IndiaMapGenerator
from .data.pollution import PollutionDataFetcher
from .data.sources import SourceRegistry
from .data.geo_utils import GeoUtils

cfg = EnforcementConfig()


class EnforcementPipeline:
    def __init__(self):
        self.detector = HotspotDetector()
        self.attributor = SourceAttributor()
        self.explainer = ExplainableAI()
        self.recommender = EnforcementRecommender()
        self.prioritizer = HotspotPrioritizer()
        self.pollution = PollutionDataFetcher()
        self.source_registry = SourceRegistry()
        self.geo_utils = GeoUtils()

    def run(self, scan_all: bool = True) -> Dict:
        print("=" * 60)
        print("  ENFORCEMENT INTELLIGENCE & PRIORITISATION AGENT")
        print("=" * 60)

        print("\n[1/5] Scanning for pollution hotspots...")
        hotspots = self.detector.scan_notable_locations() if scan_all else []
        if not hotspots:
            locs = self.detector.satellite.get_notable_locations()[:10]
            for loc in locs:
                hs = self.detector.scan_location(loc["lat"], loc["lon"], loc["name"])
                if hs:
                    hotspots.append(hs)
        hotspots = hotspots[:cfg.max_hotspots]
        print(f"  Detected {len(hotspots)} hotspots")

        for hs in hotspots:
            print(f"    {hs.location_name}: {hs.dominant_pollutant} ({hs.severity_label}, score={hs.severity_score:.2f})")

        print("\n[2/5] Attributing pollution sources...")
        attributions = []
        for hs in hotspots:
            attr = self.attributor.attribute(hs)
            attributions.append(attr)
            print(f"  {hs.location_name} -> {attr.most_probable_cause} ({attr.confidence:.1%})")

        print("\n[3/5] Generating explanations...")
        explanations = []
        for hs, attr in zip(hotspots, attributions):
            exp = self.explainer.explain(hs, attr)
            explanations.append(exp)
        print(f"  Generated {len(explanations)} explanations")

        print("\n[4/5] Creating enforcement recommendations...")
        recommendations = []
        for hs, attr in zip(hotspots, attributions):
            pop = self.pollution.get_population_exposure(hs.lat, hs.lon)
            rec = self.recommender.generate(hs, attr, pop["population"])
            recommendations.append(rec)
        print(f"  Generated {len(recommendations)} recommendations")

        print("\n[5/5] Prioritising and ranking...")
        prioritized = self.prioritizer.prioritize(recommendations)
        for rec in prioritized[:5]:
            print(f"  #{rec.priority}: {rec.location_name} — {rec.recommendation[:60]}...")

        print("\n" + "-" * 60)
        print("Generating visualizations...")

        cfg.artifacts_dir.mkdir(parents=True, exist_ok=True)
        cfg.viz_dir.mkdir(parents=True, exist_ok=True)
        cfg.geojson_dir.mkdir(parents=True, exist_ok=True)

        plots = EnforcementPlots()
        plots.plot_severity_distribution(hotspots, cfg.viz_dir / "severity_distribution.png")
        plots.plot_source_attribution(attributions, cfg.viz_dir / "source_attribution.png")
        plots.plot_confidence_distribution(attributions, cfg.viz_dir / "confidence_distribution.png")
        plots.plot_priority_ranking(prioritized, cfg.viz_dir / "priority_ranking.png")
        plots.plot_hotspot_map(hotspots, cfg.viz_dir / "hotspot_map.png")
        plots.plot_confidence_by_source(attributions, cfg.viz_dir / "confidence_by_source.png")
        print("  Static plots saved to artifacts/visualizations/")

        map_gen = IndiaMapGenerator()
        map_html = map_gen.generate_map(hotspots, attributions, prioritized,
                                         cfg.artifacts_dir / "enforcement_dashboard.html")
        print("  Interactive map saved to artifacts/enforcement_dashboard.html")

        results = {
            "timestamp": datetime.now().isoformat(),
            "total_hotspots": len(hotspots),
            "hotspots": [hs.to_dict() for hs in hotspots],
            "attributions": [a.to_dict() for a in attributions],
            "explanations": [e.to_dict() for e in explanations],
            "recommendations": [r.to_dict() for r in prioritized],
        }

        json_path = cfg.artifacts_dir / "results.json"
        json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nResults saved to {json_path}")

        print("\n" + "=" * 60)
        print("  ENFORCEMENT INTELLIGENCE PIPELINE COMPLETE")
        print("=" * 60)

        return results
