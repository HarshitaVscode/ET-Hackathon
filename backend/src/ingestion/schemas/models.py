from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PollutantType(str, Enum):
    PM2_5 = "pm2_5"
    PM10 = "pm10"
    NO2 = "no2"
    SO2 = "so2"
    CO = "co"
    O3 = "o3"
    NH3 = "nh3"
    BTX = "btx"


class AQICategory(str, Enum):
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    MODERATE = "moderate"
    POOR = "poor"
    VERY_POOR = "very_poor"
    SEVERE = "severe"
    HAZARDOUS = "hazardous"


class SensorQuality(str, Enum):
    REFERENCE = "reference"
    REGULATORY = "regulatory"
    LOW_COST = "low_cost"
    ESTIMATED = "estimated"


class SatellitePlatform(str, Enum):
    SENTINEL_2 = "sentinel_2"
    SENTINEL_5P = "sentinel_5p"
    MODIS_TERRA = "modis_terra"
    MODIS_AQUA = "modis_aqua"
    VIIRS = "viirs"
    LANDSAT_8 = "landsat_8"
    LANDSAT_9 = "landsat_9"
    RESOURCESAT_OCM3 = "resourcesat_ocm3"
    CARTOSAT_3 = "cartosat_3"


class SourceType(str, Enum):
    TRAFFIC = "traffic"
    INDUSTRY = "industry"
    CONSTRUCTION = "construction"
    AGRICULTURAL_BURNING = "agricultural_burning"
    WASTE_BURNING = "waste_burning"
    DOMESTIC_COOKING = "domestic_cooking"
    DUST = "dust"
    POWER_PLANT = "power_plant"
    BRICK_KILN = "brick_kiln"
    OTHER = "other"


class SensorReading(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier")
    station_name: str | None = None
    city: str
    ward: str | None = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime
    pollutant: PollutantType
    concentration: float = Field(..., ge=0, description="Concentration in μg/m³ or ppb")
    unit: str = "μg/m³"
    sensor_quality: SensorQuality = SensorQuality.LOW_COST
    temperature_celsius: float | None = None
    humidity_percent: float | None = Field(None, ge=0, le=100)
    wind_speed_ms: float | None = Field(None, ge=0)
    wind_direction_degrees: int | None = Field(None, ge=0, le=360)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SatelliteScene(BaseModel):
    scene_id: str = Field(..., description="Unique scene identifier")
    platform: SatellitePlatform
    acquisition_time: datetime
    processing_level: str = "L2A"
    bounding_box: tuple[float, float, float, float]
    cloud_cover_percent: float = Field(..., ge=0, le=100)
    bands_available: list[str] = Field(default_factory=list)
    data_url: str = Field(..., description="S3/STAC URL to the asset")
    file_format: str = "GeoTIFF"
    size_mb: float | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class WeatherObservation(BaseModel):
    source: str = Field(..., description="Source system (ERA5, IMD, CAMS)")
    timestamp: datetime
    latitude: float
    longitude: float
    temperature_celsius: float | None = None
    relative_humidity_percent: float | None = None
    pressure_hpa: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_degrees: int | None = None
    boundary_layer_height_m: float | None = None
    precipitation_mm: float | None = None
    solar_radiation_wm2: float | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class TrafficSnapshot(BaseModel):
    road_segment_id: str
    road_name: str | None = None
    city: str
    timestamp: datetime
    average_speed_kph: float = Field(..., ge=0)
    congestion_level: float = Field(..., ge=0, le=10, description="0=empty, 10=gridlock")
    vehicle_count_estimated: int | None = None
    road_type: str | None = None
    geometry_linestring: str | None = Field(None, description="WKT linestring")
    travel_time_seconds: int | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("congestion_level")
    @classmethod
    def clamp_congestion(cls, v: float) -> float:
        return max(0.0, min(10.0, v))


class CitizenReport(BaseModel):
    report_id: str
    citizen_id: str | None = None
    city: str
    ward: str | None = None
    latitude: float
    longitude: float
    timestamp: datetime
    report_type: str = Field(..., description="burning, construction, smell, haze, etc.")
    description: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    smell_type: str | None = None
    severity_rating: int | None = Field(None, ge=1, le=5)
    device_id: str | None = None
    verification_status: str = "pending"
    trust_score: float | None = Field(None, ge=0, le=1000)


class AQIForecast(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    forecast_horizon_hours: int
    aqi_predicted: float
    aqi_upper_bound: float
    aqi_lower_bound: float
    pm2_5_predicted: float | None = None
    pm10_predicted: float | None = None
    confidence_score: float = Field(..., ge=0, le=1)
    model_version: str | None = None


class SourceContribution(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    contributions: dict[SourceType, float] = Field(
        ..., description="Mapping of source type to percentage contribution"
    )
    total_pm25: float
    causal_confidence: float = Field(..., ge=0, le=1)
    model_version: str | None = None

    @field_validator("contributions")
    @classmethod
    def validate_contributions_sum(cls, v: dict[SourceType, float]) -> dict[SourceType, float]:
        total = sum(v.values())
        if abs(total - 100.0) > 1.0:
            raise ValueError(f"Contributions must sum to ~100%, got {total}%")
        return v
