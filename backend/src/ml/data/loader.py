from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from backend.src.ml.config import MLConfig

warnings.filterwarnings("ignore", category=UserWarning)


class AQIDatasetLoader:
    def __init__(self, config: Optional[MLConfig] = None) -> None:
        self.config = config or MLConfig()

    def _aqi_from_pollutants(self, row: pd.Series) -> float:
        sub_indices: list[float] = []
        pm25 = row.get("PM2_5", np.nan)
        pm10 = row.get("PM10", np.nan)
        no2 = row.get("NO2", np.nan)
        so2 = row.get("SO2", np.nan)
        co = row.get("CO", np.nan)
        o3 = row.get("O3", np.nan)
        nh3 = row.get("NH3", np.nan)

        if not np.isnan(pm25):
            sub_indices.append(self._pm25_sub_index(pm25))
        if not np.isnan(pm10):
            sub_indices.append(self._pm10_sub_index(pm10))
        if not np.isnan(no2):
            sub_indices.append(self._no2_sub_index(no2))
        if not np.isnan(so2):
            sub_indices.append(self._so2_sub_index(so2))
        if not np.isnan(co):
            sub_indices.append(self._co_sub_index(co))
        if not np.isnan(o3):
            sub_indices.append(self._o3_sub_index(o3))
        if not np.isnan(nh3):
            sub_indices.append(self._nh3_sub_index(nh3))

        return max(sub_indices) if sub_indices else 0.0

    @staticmethod
    def _pm25_sub_index(c: float) -> float:
        bp = [0, 30, 60, 90, 120, 250, 350, 500]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _pm10_sub_index(c: float) -> float:
        bp = [0, 50, 100, 250, 350, 430, 500, 600]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _no2_sub_index(c: float) -> float:
        bp = [0, 40, 80, 180, 280, 400, 600, 1000]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _so2_sub_index(c: float) -> float:
        bp = [0, 40, 80, 380, 800, 1200, 1600, 2000]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _co_sub_index(c: float) -> float:
        bp = [0, 1.0, 2.0, 10, 17, 34, 50, 80]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _o3_sub_index(c: float) -> float:
        bp = [0, 50, 100, 168, 208, 748, 1000, 1200]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    @staticmethod
    def _nh3_sub_index(c: float) -> float:
        bp = [0, 200, 400, 800, 1200, 1800, 2400, 3000]
        aqi = [0, 50, 100, 200, 300, 400, 500, 500]
        for i in range(len(bp) - 1):
            if bp[i] <= c <= bp[i + 1]:
                return (aqi[i + 1] - aqi[i]) / (bp[i + 1] - bp[i]) * (c - bp[i]) + aqi[i]
        return 500.0

    def generate_synthetic_dataset(self, n_samples: Optional[int] = None) -> pd.DataFrame:
        n = n_samples or self.config.n_synthetic_samples
        rng = np.random.default_rng(self.config.random_state)

        start_date = pd.Timestamp("2020-01-01")
        end_date = pd.Timestamp("2024-12-31")
        date_range = pd.date_range(start=start_date, end=end_date, periods=n)

        hour = rng.integers(0, 24, n)
        month = date_range.month.to_numpy()
        day_of_year = date_range.dayofyear.to_numpy()
        season = np.where(np.isin(month, [12, 1, 2]), 0, np.where(np.isin(month, [3, 4, 5]), 1,
                         np.where(np.isin(month, [6, 7, 8]), 2, 3)))

        seasonal_factor = np.where(
            season == 0, 1.3, np.where(season == 1, 0.8, np.where(season == 2, 0.9, 1.1))
        )
        diurnal_factor = 1.0 + 0.3 * np.sin(np.pi * (hour - 8) / 12)
        weekend_factor = np.where(date_range.dayofweek.to_numpy() >= 5, 0.85, 1.0)

        base_noise = rng.normal(0, 0.05, n)

        pm25_base = 60.0 * seasonal_factor * diurnal_factor * weekend_factor
        pm25_base *= (1.0 + base_noise)
        pm25 = np.clip(pm25_base + rng.normal(0, 5, n), 0, 500)

        pm10 = pm25 * rng.uniform(1.2, 2.0, n) + rng.normal(0, 10, n)
        pm10 = np.clip(pm10, 0, 600)

        no = pm25 * rng.uniform(0.3, 0.8, n) * diurnal_factor + rng.normal(0, 5, n)
        no = np.clip(no, 0, 200)

        no2_base = 40.0 * seasonal_factor * diurnal_factor * weekend_factor
        no2 = np.clip(no2_base * (1.0 + rng.normal(0, 0.15, n)), 0, 400)

        so2 = np.clip(rng.exponential(15, n) * seasonal_factor + rng.normal(0, 3, n), 0, 200)

        co = np.clip(
            rng.lognormal(mean=0.5, sigma=0.4, size=n) * diurnal_factor * seasonal_factor,
            0, 50,
        )

        o3 = np.clip(
            40 + 20 * np.sin(np.pi * (hour - 12) / 8) + rng.normal(0, 8, n) * (1 / seasonal_factor),
            0, 300,
        )

        nh3 = np.clip(rng.exponential(20, n) + rng.normal(0, 5, n), 0, 500)

        benzene = np.clip(rng.lognormal(mean=0.8, sigma=0.5, size=n), 0, 50)
        toluene = benzene * rng.uniform(1.5, 3.0, n)
        xylene = benzene * rng.uniform(0.5, 1.5, n)

        temperature = 25 + 10 * np.sin(np.pi * (month - 6) / 6) + 5 * np.sin(np.pi * (hour - 14) / 12) + rng.normal(0, 2, n)
        humidity = 60 + 20 * np.cos(np.pi * (month - 8) / 6) - 10 * np.sin(np.pi * (hour - 14) / 12) + rng.normal(0, 5, n)
        humidity = np.clip(humidity, 10, 100)

        wind_speed = np.clip(rng.weibull(a=2, size=n) * 3 + 1, 0, 20)
        wind_direction = rng.uniform(0, 360, n)
        pressure = 1013 + 10 * np.cos(np.pi * (month - 1) / 6) + rng.normal(0, 3, n)
        rainfall = np.where(
            season == 2,
            rng.exponential(5, n),
            rng.exponential(0.5, n),
        )
        rainfall = np.clip(rainfall, 0, 100)
        visibility = np.clip(
            10 - 0.02 * pm25 + rng.normal(0, 1, n), 0.5, 20,
        )

        df = pd.DataFrame({
            "Date": date_range,
            "Hour": hour,
            "Day": date_range.day.to_numpy(),
            "Month": month,
            "DayOfWeek": date_range.dayofweek.to_numpy(),
            "Season": season,
            "PM2_5": np.round(pm25, 1),
            "PM10": np.round(pm10, 1),
            "NO": np.round(no, 1),
            "NO2": np.round(no2, 1),
            "SO2": np.round(so2, 1),
            "CO": np.round(co, 2),
            "O3": np.round(o3, 1),
            "NH3": np.round(nh3, 1),
            "Benzene": np.round(benzene, 2),
            "Toluene": np.round(toluene, 2),
            "Xylene": np.round(xylene, 2),
            "Temperature": np.round(temperature, 1),
            "Humidity": np.round(humidity, 1),
            "Wind_Speed": np.round(wind_speed, 1),
            "Wind_Direction": np.round(wind_direction, 1),
            "Pressure": np.round(pressure, 1),
            "Rainfall": np.round(rainfall, 1),
            "Visibility": np.round(visibility, 1),
        })

        aqi_values = df.apply(self._aqi_from_pollutants, axis=1)
        df["AQI"] = np.round(aqi_values, 1)

        return df

    def load_or_generate(self, force_generate: bool = False) -> pd.DataFrame:
        csv_path = Path(self.config.data_dir) / "aqi_data.csv"
        if csv_path.exists() and not force_generate:
            return pd.read_csv(csv_path, parse_dates=["Date"])
        df = self.generate_synthetic_dataset()
        os.makedirs(self.config.data_dir, exist_ok=True)
        df.to_csv(csv_path, index=False)
        return df
