from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class TimeseriesDB:
    def __init__(self, db_path: str = "backend/data/vayu.db"):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    def connect(self):
        self._conn = sqlite3.connect(str(self._path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def close(self):
        if self._conn:
            self._conn.close()

    def _init_schema(self):
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                station_name TEXT,
                city TEXT NOT NULL,
                ward TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                pollutant TEXT NOT NULL,
                concentration REAL NOT NULL,
                unit TEXT DEFAULT 'μg/m³',
                sensor_quality TEXT DEFAULT 'low_cost',
                temperature_celsius REAL,
                humidity_percent REAL,
                wind_speed_ms REAL,
                wind_direction_degrees INTEGER,
                raw_payload TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_sensor_time ON sensor_readings(sensor_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_sensor_pollutant ON sensor_readings(pollutant, timestamp);
            CREATE INDEX IF NOT EXISTS idx_sensor_city ON sensor_readings(city, timestamp);

            CREATE TABLE IF NOT EXISTS weather_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                temperature_celsius REAL,
                relative_humidity_percent REAL,
                pressure_hpa REAL,
                wind_speed_ms REAL,
                wind_direction_degrees INTEGER,
                boundary_layer_height_m REAL,
                precipitation_mm REAL,
                solar_radiation_wm2 REAL,
                raw_payload TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_observations(timestamp);

            CREATE TABLE IF NOT EXISTS traffic_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                road_segment_id TEXT NOT NULL,
                road_name TEXT,
                city TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                average_speed_kph REAL NOT NULL,
                congestion_level REAL NOT NULL,
                vehicle_count_estimated INTEGER,
                road_type TEXT,
                raw_payload TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_traffic_time ON traffic_snapshots(road_segment_id, timestamp);

            CREATE TABLE IF NOT EXISTS citizen_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                citizen_id TEXT,
                city TEXT NOT NULL,
                ward TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                report_type TEXT NOT NULL,
                description TEXT,
                image_urls TEXT DEFAULT '[]',
                severity_rating INTEGER,
                verification_status TEXT DEFAULT 'pending',
                trust_score REAL DEFAULT 500,
                raw_payload TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_reports_time ON citizen_reports(timestamp);
            CREATE INDEX IF NOT EXISTS idx_reports_status ON citizen_reports(verification_status);

            CREATE TABLE IF NOT EXISTS aqi_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                forecast_horizon_hours INTEGER NOT NULL,
                aqi_predicted REAL NOT NULL,
                aqi_upper_bound REAL,
                aqi_lower_bound REAL,
                pm2_5_predicted REAL,
                pm10_predicted REAL,
                confidence_score REAL,
                model_version TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_forecast_time ON aqi_forecasts(timestamp, forecast_horizon_hours);

            CREATE TABLE IF NOT EXISTS source_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,
                contributions TEXT NOT NULL,
                total_pm25 REAL NOT NULL,
                causal_confidence REAL NOT NULL,
                model_version TEXT
            );

            CREATE TABLE IF NOT EXISTS feature_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ttl_seconds INTEGER DEFAULT 300
            );
        """)
        self._conn.commit()

    def insert_sensor_reading(self, data: dict[str, Any]) -> int:
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO sensor_readings
                (sensor_id, station_name, city, ward, latitude, longitude,
                 timestamp, pollutant, concentration, unit, sensor_quality,
                 temperature_celsius, humidity_percent, wind_speed_ms,
                 wind_direction_degrees, raw_payload)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("sensor_id"), data.get("station_name"), data.get("city", ""),
            data.get("ward"), data.get("latitude"), data.get("longitude"),
            data.get("timestamp"), data.get("pollutant"), data.get("concentration"),
            data.get("unit", "μg/m³"), data.get("sensor_quality", "low_cost"),
            data.get("temperature_celsius"), data.get("humidity_percent"),
            data.get("wind_speed_ms"), data.get("wind_direction_degrees"),
            json.dumps(data.get("raw_payload", {})),
        ))
        self._conn.commit()
        return cur.lastrowid

    def insert_weather(self, data: dict[str, Any]) -> int:
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO weather_observations
                (source, timestamp, latitude, longitude, temperature_celsius,
                 relative_humidity_percent, pressure_hpa, wind_speed_ms,
                 wind_direction_degrees, boundary_layer_height_m,
                 precipitation_mm, solar_radiation_wm2, raw_payload)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("source"), data.get("timestamp"), data.get("latitude"),
            data.get("longitude"), data.get("temperature_celsius"),
            data.get("relative_humidity_percent"), data.get("pressure_hpa"),
            data.get("wind_speed_ms"), data.get("wind_direction_degrees"),
            data.get("boundary_layer_height_m"), data.get("precipitation_mm"),
            data.get("solar_radiation_wm2"), json.dumps(data.get("raw_payload", {})),
        ))
        self._conn.commit()
        return cur.lastrowid

    def insert_traffic(self, data: dict[str, Any]) -> int:
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO traffic_snapshots
                (road_segment_id, road_name, city, timestamp, average_speed_kph,
                 congestion_level, vehicle_count_estimated, road_type, raw_payload)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data.get("road_segment_id"), data.get("road_name"), data.get("city"),
            data.get("timestamp"), data.get("average_speed_kph"),
            data.get("congestion_level"), data.get("vehicle_count_estimated"),
            data.get("road_type"), json.dumps(data.get("raw_payload", {})),
        ))
        self._conn.commit()
        return cur.lastrowid

    def insert_citizen_report(self, data: dict[str, Any]) -> int:
        cur = self._conn.cursor()
        cur.execute("""
            INSERT INTO citizen_reports
                (report_id, citizen_id, city, ward, latitude, longitude,
                 timestamp, report_type, description, image_urls,
                 severity_rating, verification_status, trust_score, raw_payload)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("report_id"), data.get("citizen_id"), data.get("city"),
            data.get("ward"), data.get("latitude"), data.get("longitude"),
            data.get("timestamp"), data.get("report_type"), data.get("description"),
            json.dumps(data.get("image_urls", [])), data.get("severity_rating"),
            data.get("verification_status", "pending"), data.get("trust_score", 500),
            json.dumps(data.get("raw_payload", {})),
        ))
        self._conn.commit()
        return cur.lastrowid

    def set_feature(self, key: str, value: Any, ttl_seconds: int = 300):
        cur = self._conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO feature_store (key, value, timestamp, ttl_seconds)
            VALUES (?, ?, ?, ?)
        """, (key, json.dumps(value), datetime.now(timezone.utc).isoformat(), ttl_seconds))
        self._conn.commit()

    def get_feature(self, key: str) -> Any | None:
        cur = self._conn.cursor()
        cur.execute("SELECT value, timestamp, ttl_seconds FROM feature_store WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def query_sensor_readings(self, sensor_id: str | None = None, pollutant: str | None = None,
                               limit: int = 100, hours: int | None = None) -> list[dict[str, Any]]:
        cur = self._conn.cursor()
        conditions = []
        params = []
        if sensor_id:
            conditions.append("sensor_id = ?")
            params.append(sensor_id)
        if pollutant:
            conditions.append("pollutant = ?")
            params.append(pollutant)
        if hours:
            conditions.append("timestamp >= datetime('now', ?)")
            params.append(f"-{hours} hours")
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        cur.execute(f"SELECT * FROM sensor_readings{where} ORDER BY timestamp DESC LIMIT ?", params + [limit])
        return [dict(r) for r in cur.fetchall()]

    def query_forecasts(self, hours: int = 72) -> list[dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("""
            SELECT * FROM aqi_forecasts
            WHERE forecast_horizon_hours <= ?
            ORDER BY timestamp DESC, forecast_horizon_hours ASC
        """, (hours,))
        return [dict(r) for r in cur.fetchall()]
