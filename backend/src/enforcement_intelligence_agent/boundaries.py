"""Load real GIS boundary data for India maps."""
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .config import EnforcementConfig

_cfg = EnforcementConfig()


def _load_geojson(name: str):
    path = _cfg.geojson_dir / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"type": "FeatureCollection", "features": []}


def get_india_boundary() -> Dict:
    return _load_geojson("india_boundary.json")


def get_state_boundaries() -> Dict:
    return _load_geojson("india_states.json")


def get_district_boundaries() -> Dict:
    return _load_geojson("india_districts.json")


def get_state_boundary_polygons() -> List[Tuple[str, List, List]]:
    result = []
    for feat in get_state_boundaries().get("features", []):
        coords = feat["geometry"]["coordinates"][0]
        result.append((
            feat["properties"]["name"],
            [c[0] for c in coords],
            [c[1] for c in coords],
        ))
    return result


def get_india_outline_polygons() -> List[Tuple[List, List]]:
    result = []
    for feat in get_india_boundary().get("features", []):
        coords = feat["geometry"]["coordinates"][0]
        result.append(([c[0] for c in coords], [c[1] for c in coords]))
    return result
