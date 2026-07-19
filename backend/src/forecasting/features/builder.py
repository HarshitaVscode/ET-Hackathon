from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame, group_col: str = "location_id") -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for _, grp in df.groupby(group_col):
        grp = grp.sort_values("datetime").reset_index(drop=True)
        grp = _add_lag_features(grp)
        grp = _add_rolling_features(grp)
        grp = _add_cyclical_features(grp)
        grp = _add_indicator_features(grp)
        grp = _add_season_dummies(grp)
        rows.append(grp)

    result = pd.concat(rows, ignore_index=True)
    return result


def _add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    aqi = df["AQI"].values
    for lag in [1, 2, 3, 6, 12, 24, 48, 72]:
        shifted = np.full(len(aqi), np.nan)
        if lag < len(aqi):
            shifted[lag:] = aqi[:-lag]
        df[f"AQI_lag_{lag}"] = np.round(shifted, 1)
    return df


def _add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    aqi = df["AQI"].values
    for window in [6, 24, 72]:
        mean_vals = np.full(len(aqi), np.nan)
        for i in range(window, len(aqi)):
            mean_vals[i] = np.mean(aqi[i - window : i])
        df[f"AQI_rolling_mean_{window}"] = np.round(mean_vals, 1)

    max_vals = np.full(len(aqi), np.nan)
    min_vals = np.full(len(aqi), np.nan)
    for i in range(24, len(aqi)):
        max_vals[i] = np.max(aqi[i - 24 : i])
        min_vals[i] = np.min(aqi[i - 24 : i])
    df["AQI_rolling_max_24"] = np.round(max_vals, 1)
    df["AQI_rolling_min_24"] = np.round(min_vals, 1)
    return df


def _add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    hour = df["Hour"].values
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    if "Day" in df.columns:
        day = df["Day"].values
        df["day_sin"] = np.sin(2 * np.pi * day / 31)
        df["day_cos"] = np.cos(2 * np.pi * day / 31)

    if "Month" in df.columns:
        month = df["Month"].values
        df["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12)
        df["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12)

    if "DayOfWeek" in df.columns:
        dow = df["DayOfWeek"].values
        df["dayofweek_sin"] = np.sin(2 * np.pi * dow / 7)
        df["dayofweek_cos"] = np.cos(2 * np.pi * dow / 7)

    hourly_diff = np.full(len(df), np.nan)
    aqi = df["AQI"].values
    for i in range(1, len(aqi)):
        hourly_diff[i] = aqi[i] - aqi[i - 1]
    df["AQI_hourly_diff"] = np.round(hourly_diff, 1)

    daily_diff = np.full(len(df), np.nan)
    for i in range(24, len(aqi)):
        daily_diff[i] = aqi[i] - aqi[i - 24]
    df["AQI_daily_diff"] = np.round(daily_diff, 1)
    return df


def _add_indicator_features(df: pd.DataFrame) -> pd.DataFrame:
    df["is_weekend"] = np.where(df["DayOfWeek"].values >= 5, 1, 0)
    hour = df["Hour"].values
    df["is_rush_hour"] = np.where(((hour >= 7) & (hour <= 10)) | ((hour >= 17) & (hour <= 20)), 1, 0)
    return df


def _add_season_dummies(df: pd.DataFrame) -> pd.DataFrame:
    season = df["Season"].values
    for s in range(4):
        df[f"season_{['winter','spring','summer','autumn'][s]}"] = (season == s).astype(int)
    return df
