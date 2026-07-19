from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


def prepare_features(
    sensor_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    static_df: pd.DataFrame,
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
) -> dict[str, Any]:
    num_nodes = len(grid_lats)

    if sensor_df.empty:
        pm25 = np.full(num_nodes, 100.0)
    else:
        sensor_col = sensor_df.get("pm2_5", sensor_df.get("concentration", [100]))
        pm25 = np.full(num_nodes, float(sensor_col.mean() if hasattr(sensor_col, 'mean') else sensor_col[0]))

    if weather_df.empty:
        temperature = np.full(num_nodes, 30.0)
        humidity = np.full(num_nodes, 55.0)
        wind_speed = np.full(num_nodes, 3.5)
        wind_dir = np.full(num_nodes, 180.0)
        pbl_height = np.full(num_nodes, 1000.0)
        precipitation = np.full(num_nodes, 0.0)
    else:
        temperature = np.full(num_nodes, float(weather_df.get("temperature_celsius", [30]).iloc[0] if hasattr(weather_df, 'iloc') and not weather_df.empty else 30))
        humidity = np.full(num_nodes, float(weather_df.get("relative_humidity_percent", [55]).iloc[0] if hasattr(weather_df, 'iloc') and not weather_df.empty else 55))
        wind_speed = np.full(num_nodes, float(weather_df.get("wind_speed_ms", [3.5]).iloc[0] if hasattr(weather_df, 'iloc') and not weather_df.empty else 3.5))
        wind_dir = np.full(num_nodes, 180.0)
        pbl_height = np.full(num_nodes, 1000.0)
        precipitation = np.full(num_nodes, 0.0)

    if static_df.empty:
        elevation = np.full(num_nodes, 200.0)
        land_use = np.full(num_nodes, 1.0)
        road_density = np.full(num_nodes, 0.3)
        population = np.full(num_nodes, 5000.0)
        industrial_area = np.full(num_nodes, 0.1)
        green_cover = np.full(num_nodes, 0.2)
    else:
        elevation = np.full(num_nodes, float(static_df.get("elevation", [200]).iloc[0] if hasattr(static_df, 'iloc') and not static_df.empty else 200))
        land_use = np.full(num_nodes, 1.0)
        road_density = np.full(num_nodes, 0.3)
        population = np.full(num_nodes, 5000.0)
        industrial_area = np.full(num_nodes, 0.1)
        green_cover = np.full(num_nodes, 0.2)

    node_features = np.column_stack([
        pm25,
        temperature,
        humidity,
        wind_speed,
        wind_dir,
        pbl_height,
        precipitation,
        elevation,
        land_use,
        road_density,
        population,
        industrial_area,
        green_cover,
        grid_lats,
        grid_lons,
    ]).astype(np.float32)

    rng = np.random.default_rng(seed=42)
    num_edges = num_nodes * 8
    src = rng.integers(0, num_nodes, num_edges)
    dst = rng.integers(0, num_nodes, num_edges)
    edge_index = np.stack([src, dst], axis=0).astype(np.int64)

    return {
        "node_features": node_features,
        "edge_index": edge_index,
        "time_idx": np.array([96]),
    }
