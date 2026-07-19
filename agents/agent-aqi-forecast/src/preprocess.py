"""Feature preprocessing for the AQI Forecast Agent."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


def build_city_graph(
    lats: np.ndarray,
    lons: np.ndarray,
    k_neighbors: int = 8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a k-nearest-neighbor graph of city grid cells.

    Args:
        lats: [n] latitude array
        lons: [n] longitude array
        k_neighbors: number of nearest neighbors per node

    Returns:
        edge_index: [2, E] adjacency in COO format
        edge_weight: [E] distance-weighted edge weights
        node_positions: [n, 2] node coordinates
    """
    n = len(lats)
    coords = np.column_stack([lats, lons])

    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=min(k_neighbors + 1, n), metric="haversine")
    nn.fit(np.radians(coords))

    distances, indices = nn.kneighbors(np.radians(coords))

    src = []
    dst = []
    weights = []
    for i in range(n):
        for j in range(1, min(k_neighbors + 1, n)):
            if indices[i, j] != i:
                src.append(i)
                dst.append(indices[i, j])
                w = np.exp(-distances[i, j] * 100)  # Distance decay
                weights.append(w)

    edge_index = np.array([src, dst], dtype=np.int64)
    return edge_index, np.array(weights, dtype=np.float32), coords


def prepare_features(
    sensor_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    static_df: pd.DataFrame,
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
    timestamp: datetime | None = None,
) -> dict[str, np.ndarray]:
    """Prepare model input features from raw data.

    Returns:
        dict with 'node_features', 'edge_index', 'edge_weight', 'time_idx'
    """
    n_grid = len(grid_lats)

    # Weather features (interpolate to grid)
    weather_features = _interpolate_to_grid(weather_df, grid_lats, grid_lons)
    node_features = np.zeros((n_grid, weather_features.shape[1] + len(static_df.columns)))

    # Static features (broadcast)
    for i in range(n_grid):
        node_features[i, :weather_features.shape[1]] = weather_features[i]
        for j, col in enumerate(static_df.columns):
            node_features[i, weather_features.shape[1] + j] = static_df[col].iloc[0]

    # Build graph
    edge_index, edge_weight, _ = build_city_graph(grid_lats, grid_lons)

    # Time index
    now = timestamp or datetime.now(timezone.utc)
    time_idx = now.hour + now.weekday() * 24

    return {
        "node_features": node_features.astype(np.float32),
        "edge_index": edge_index.astype(np.int64),
        "edge_weight": edge_weight,
        "time_idx": np.array([time_idx], dtype=np.int64),
    }


def _interpolate_to_grid(
    df: pd.DataFrame,
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
) -> np.ndarray:
    """Interpolate sparse weather measurements to the city grid."""
    if df.empty:
        n_grid = len(grid_lats)
        n_feats = 6
        return np.zeros((n_grid, n_feats))

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    numeric_cols = [c for c in numeric_cols if c not in ("latitude", "longitude")]

    n_feats = len(numeric_cols) or 1
    n_grid = len(grid_lats)
    result = np.zeros((n_grid, n_feats))

    if not numeric_cols:
        return result

    from scipy.interpolate import RBFInterpolator
    points = df[["latitude", "longitude"]].values
    for i, col in enumerate(numeric_cols):
        values = df[col].values
        if len(points) < 4:
            result[:, i] = np.nanmean(values)
        else:
            interp = RBFInterpolator(points, values, epsilon=0.1)
            result[:, i] = interp(np.column_stack([grid_lats, grid_lons]))

    return np.nan_to_num(result, nan=0.0)
