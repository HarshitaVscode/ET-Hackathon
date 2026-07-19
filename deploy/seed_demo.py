"""Demo data seeding script for hackathon presentation.

Writes directly to the event bus, SQLite database, and graph store.
No Kafka, no Neo4j, no TimescaleDB required.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from random import Random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from src.infrastructure.event_bus import get_event_bus
from src.infrastructure.database import TimeseriesDB

rng = Random(42)

WARDS = {
    "W01": {"name": "Civil Lines", "lat": 28.68, "lon": 77.22},
    "W02": {"name": "Karol Bagh", "lat": 28.65, "lon": 77.19},
    "W03": {"name": "New Delhi", "lat": 28.61, "lon": 77.21},
    "W04": {"name": "Vasant Kunj", "lat": 28.53, "lon": 77.15},
    "W05": {"name": "Dwarka", "lat": 28.59, "lon": 77.05},
    "W06": {"name": "Rohini", "lat": 28.73, "lon": 77.12},
    "W07": {"name": "Najafgarh", "lat": 28.61, "lon": 76.98},
    "W08": {"name": "Moti Nagar", "lat": 28.66, "lon": 77.14},
    "W09": {"name": "Shahdara", "lat": 28.68, "lon": 77.29},
    "W10": {"name": "East Delhi", "lat": 28.62, "lon": 77.29},
    "W11": {"name": "South Delhi", "lat": 28.55, "lon": 77.22},
    "W12": {"name": "Ghaziabad", "lat": 28.66, "lon": 77.43},
}

NUM_DAYS = 7


def generate_aqi(base: float, hour: float, noise: float = 20) -> float:
    diurnal = -30 * math.sin(2 * math.pi * (hour - 14) / 24)
    return max(0, base + diurnal + rng.gauss(0, noise))


async def seed_data() -> None:
    event_bus = get_event_bus()
    await event_bus.start()

    db = TimeseriesDB("backend/data/vayu.db")
    db.connect()

    now = datetime.now(timezone.utc)
    total_messages = 0

    print(f"Seeding {NUM_DAYS} days of demo data...")

    for day_offset in range(NUM_DAYS):
        date = now - timedelta(days=NUM_DAYS - day_offset)
        for hour in range(24):
            timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            ts_iso = timestamp.isoformat()

            for ward_id, ward in WARDS.items():
                base_aqi = 250 if ward_id in ("W10", "W12") else 180 if ward_id in ("W09", "W06") else 150
                aqi = generate_aqi(base_aqi, hour)
                pm25 = aqi / 2.0 + rng.gauss(0, 5)
                pm10 = pm25 * 1.8 + rng.gauss(0, 10)

                msg = {
                    "sensor_id": f"CPCB-{ward_id}",
                    "station_name": f"{ward['name']} CAAQMS",
                    "city": "Delhi",
                    "ward": ward_id,
                    "latitude": ward["lat"],
                    "longitude": ward["lon"],
                    "timestamp": ts_iso,
                    "pollutant": "pm2_5",
                    "concentration": round(pm25, 1),
                    "unit": "μg/m³",
                    "sensor_quality": "reference",
                    "temperature_celsius": round(30 + 5 * math.sin(math.pi * (hour - 12) / 12) + rng.gauss(0, 2), 1),
                    "humidity_percent": round(55 - 15 * math.sin(math.pi * (hour - 12) / 12) + rng.gauss(0, 5), 1),
                }
                await event_bus.publish("raw.sensor", msg, key=f"CPCB-{ward_id}")
                db.insert_sensor_reading(msg)
                total_messages += 1

                msg10 = dict(msg, pollutant="pm10", concentration=round(pm10, 1))
                await event_bus.publish("raw.sensor", msg10, key=f"CPCB-{ward_id}")
                db.insert_sensor_reading(msg10)
                total_messages += 1

            for grid in range(6):
                lat = 28.40 + grid * 0.08
                lon = 76.84 + grid * 0.10
                weather = {
                    "source": "ERA5",
                    "timestamp": ts_iso,
                    "latitude": round(lat, 4),
                    "longitude": round(lon, 4),
                    "temperature_celsius": round(30 + 5 * math.sin(math.pi * (hour - 12) / 12), 1),
                    "relative_humidity_percent": round(55 - 15 * math.sin(math.pi * (hour - 12) / 12), 1),
                    "wind_speed_ms": round(rng.uniform(1, 6), 1),
                    "wind_direction_degrees": rng.randint(0, 359),
                    "boundary_layer_height_m": round(rng.uniform(500, 1800)),
                }
                await event_bus.publish("raw.weather", weather)
                db.insert_weather(weather)
                total_messages += 1

            roads = [
                ("NH9", 28.66, 77.35),
                ("Ring_Road", 28.58, 77.25),
                ("MG_Road", 28.48, 77.10),
                ("AIIMS", 28.57, 77.21),
            ]
            for road_name, lat, lon in roads:
                congestion = 3 + 5 * math.exp(-((hour - 9) ** 2) / 50) + 4 * math.exp(-((hour - 18) ** 2) / 30) + rng.gauss(0, 0.5)
                traffic = {
                    "road_segment_id": road_name,
                    "road_name": road_name,
                    "city": "Delhi",
                    "timestamp": ts_iso,
                    "average_speed_kph": round(50 / max(1, congestion), 1),
                    "congestion_level": round(min(10, congestion), 1),
                }
                await event_bus.publish("raw.traffic", traffic)
                db.insert_traffic(traffic)
                total_messages += 1

        if day_offset % 2 == 0:
            print(f"  ... {day_offset + 1}/{NUM_DAYS} days seeded ({total_messages} messages)")

    for _ in range(20):
        ward_id = rng.choice(list(WARDS.keys()))
        ward = WARDS[ward_id]
        report = {
            "report_id": f"CR-DEMO-{rng.randint(1000, 9999)}",
            "citizen_id": f"CIT-{rng.randint(100, 999)}",
            "city": "Delhi",
            "ward": ward_id,
            "latitude": ward["lat"] + rng.gauss(0, 0.01),
            "longitude": ward["lon"] + rng.gauss(0, 0.01),
            "timestamp": (now - timedelta(hours=rng.randint(0, 48))).isoformat(),
            "report_type": rng.choice(["burning", "smell", "construction", "haze"]),
            "description": rng.choice([
                "Burning smell in the air",
                "Visible smoke near the fields",
                "Construction dust everywhere",
                "Thick haze reducing visibility",
            ]),
            "severity_rating": rng.randint(2, 5),
            "verification_status": rng.choice(["pending", "verified", "verified", "rejected"]),
        }
        await event_bus.publish("raw.citizen", report)
        db.insert_citizen_report(report)
        total_messages += 1

    db.close()
    await event_bus.stop()

    print(f"\n Done! Seeded {total_messages} messages across 5 topics")
    print(f"   Topics: raw.sensor, raw.weather, raw.traffic, raw.satellite, raw.citizen")
    print(f"   Data: {NUM_DAYS} days, {len(WARDS)} wards, 4 road segments")


def main() -> None:
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
