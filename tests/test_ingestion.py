from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.ingestion.schemas.models import (
    PollutantType,
    SensorQuality,
    SensorReading,
    SourceType,
    SourceContribution,
)


class TestSensorReading:
    def test_create_valid(self):
        reading = SensorReading(
            sensor_id="CPCB-DL-001",
            city="Delhi",
            ward="W12",
            latitude=28.61,
            longitude=77.23,
            timestamp=datetime.now(timezone.utc),
            pollutant=PollutantType.PM2_5,
            concentration=128.5,
            sensor_quality=SensorQuality.REFERENCE,
        )
        assert reading.sensor_id == "CPCB-DL-001"
        assert reading.pollutant == PollutantType.PM2_5
        assert reading.concentration == 128.5

    def test_serialization(self):
        reading = SensorReading(
            sensor_id="CPCB-DL-001",
            city="Delhi",
            latitude=28.61,
            longitude=77.23,
            timestamp=datetime(2026, 7, 18, 14, 30, tzinfo=timezone.utc),
            pollutant=PollutantType.PM2_5,
            concentration=100.0,
        )
        data = json.loads(reading.model_dump_json())
        assert data["sensor_id"] == "CPCB-DL-001"
        assert data["pollutant"] == "pm2_5"
        assert data["concentration"] == 100.0

    def test_invalid_latitude(self):
        with pytest.raises(ValueError):
            SensorReading(
                sensor_id="x", city="x", latitude=100, longitude=0,
                timestamp=datetime.now(timezone.utc),
                pollutant=PollutantType.PM2_5, concentration=10,
            )


class TestSourceContribution:
    def test_valid_contributions(self):
        sc = SourceContribution(
            latitude=28.61,
            longitude=77.23,
            timestamp=datetime.now(timezone.utc),
            contributions={
                SourceType.TRAFFIC: 42.0,
                SourceType.AGRICULTURAL_BURNING: 28.0,
                SourceType.INDUSTRY: 18.0,
                SourceType.CONSTRUCTION: 8.0,
                SourceType.OTHER: 4.0,
            },
            total_pm25=128.5,
            causal_confidence=0.85,
        )
        assert abs(sum(sc.contributions.values()) - 100.0) < 0.01

    def test_invalid_contributions(self):
        with pytest.raises(ValueError):
            SourceContribution(
                latitude=28.61, longitude=77.23,
                timestamp=datetime.now(timezone.utc),
                contributions={SourceType.TRAFFIC: 50.0},
                total_pm25=100, causal_confidence=0.5,
            )
