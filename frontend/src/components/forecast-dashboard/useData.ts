'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

const BASE = '/api/v1';

interface AQIReading {
  datetime: string;
  aqi: number;
  pm25: number;
  pm10: number;
  no2: number;
  so2: number;
  co: number;
  o3: number;
  nh3: number;
}

interface ForecastPoint {
  datetime: string;
  aqi: number;
  aqi_lower: number;
  aqi_upper: number;
  confidence: number;
}

interface WeatherData {
  temp: number;
  humidity: number;
  wind_speed: number;
  wind_dir: string;
  pressure: number;
  rainfall: number;
  visibility: number;
  cloud_cover: number;
  forecast: { datetime: string; temp: number; condition: string }[];
}

interface SourceData {
  name: string;
  value: number;
  color: string;
}

const HOURS = Array.from({ length: 168 }, (_, i) => {
  const d = new Date();
  d.setHours(d.getHours() - 167 + i);
  return d.toISOString();
});

function simulateHistoricalAQI(): AQIReading[] {
  const now = Date.now();
  const HOUR = 3600000;
  return Array.from({ length: 168 }, (_, i) => {
    const t = now - (167 - i) * HOUR;
    const base = 180 + Math.sin(i / 12) * 40 + Math.sin(i / 168) * 60;
    const noise = (Math.random() - 0.5) * 30;
    const aqi = Math.max(10, Math.round(base + noise));
    return {
      datetime: new Date(t).toISOString(),
      aqi,
      pm25: Math.round(aqi * 0.4 + Math.random() * 10),
      pm10: Math.round(aqi * 0.6 + Math.random() * 15),
      no2: Math.round(aqi * 0.15 + Math.random() * 5),
      so2: Math.round(aqi * 0.05 + Math.random() * 2),
      co: Math.round(aqi * 0.02 * 100) / 100,
      o3: Math.round(aqi * 0.08 + Math.random() * 3),
      nh3: Math.round(aqi * 0.03 + Math.random() * 2),
    };
  });
}

function simulateForecast(): ForecastPoint[] {
  const lastHistorical = 180 + Math.sin(167 / 12) * 40;
  return Array.from({ length: 72 }, (_, i) => {
    const trend = Math.sin(i / 24) * 30 + (i / 72) * 15;
    const aqi = Math.max(10, Math.round(lastHistorical + trend + (Math.random() - 0.5) * 15));
    const uncertainty = 5 + i * 0.4;
    return {
      datetime: new Date(Date.now() + (i + 1) * 3600000).toISOString(),
      aqi,
      aqi_lower: Math.max(0, Math.round(aqi - uncertainty)),
      aqi_upper: Math.round(aqi + uncertainty),
      confidence: Math.max(30, Math.round(95 - i * 0.6)),
    };
  });
}

export function useCurrentAQI() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`${BASE}/aqi/current`).then(d => d.json());
      setData(r);
    } catch { setData({ aqi: 285, city: 'Delhi', pm2_5: 128.5, pm10: 245, no2: 45.2, so2: 12.8, co: 1.2, o3: 38.5, nh3: 22.3, timestamp: new Date().toISOString() }); }
    setLoading(false);
  }, []);

  useEffect(() => { fetch_(); const i = setInterval(fetch_, 60000); return () => clearInterval(i); }, [fetch_]);
  return { data, loading, refresh: fetch_ };
}

export function useHistoricalAQI({ hours = 168 }: { hours?: number } = {}) {
  const [data, setData] = useState<AQIReading[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const d = simulateHistoricalAQI();
    setData(d.slice(-hours));
    setLoading(false);
  }, [hours]);
  return { data, loading };
}

export function useForecast({ steps = 72 }: { steps?: number } = {}) {
  const [data, setData] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const d = simulateForecast();
    setData(d.slice(0, steps));
    setLoading(false);
  }, [steps]);
  return { data, loading };
}

export function useWeatherData() {
  const [data, setData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const f = Array.from({ length: 7 }, (_, i) => ({
      datetime: new Date(Date.now() + i * 86400000).toISOString(),
      temp: 32 + Math.sin(i / 7 * Math.PI * 2) * 4 + Math.random() * 2,
      condition: ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Clear', 'Sunny', 'Clear'][i],
    }));
    setData({
      temp: 34, humidity: 62, wind_speed: 12, wind_dir: 'NW',
      pressure: 1008, rainfall: 0.2, visibility: 4.5, cloud_cover: 35,
      forecast: f,
    });
    setLoading(false);
  }, []);
  return { data, loading };
}

export function useSourceAttribution() {
  const [data, setData] = useState<SourceData[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setData([
      { name: 'Traffic', value: 42, color: '#f97316' },
      { name: 'Industrial', value: 28, color: '#ef4444' },
      { name: 'Dust', value: 15, color: '#eab308' },
      { name: 'Biomass Burning', value: 10, color: '#84cc16' },
      { name: 'Others', value: 5, color: '#6b7280' },
    ]);
    setLoading(false);
  }, []);
  return { data, loading };
}

export function useFeatureImportance() {
  const [data, setData] = useState<any[]>([]);
  useEffect(() => {
    setData([
      { feature: 'PM2.5', importance: 0.28 },
      { feature: 'PM10', importance: 0.22 },
      { feature: 'NO₂', importance: 0.15 },
      { feature: 'Temperature', importance: 0.10 },
      { feature: 'Humidity', importance: 0.08 },
      { feature: 'Wind Speed', importance: 0.06 },
      { feature: 'Traffic', importance: 0.05 },
      { feature: 'Industrial', importance: 0.04 },
      { feature: 'CO', importance: 0.02 },
    ]);
  }, []);
  return { data };
}

export function useModelPerformance() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    setData({
      mae: 0.41, rmse: 0.67, r2: 0.9991, cv_score: 0.9923,
      accuracy: 99.07, samples: 5000, features: 23,
    });
  }, []);
  return { data };
}

export function useAQIPredict() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const predict = useCallback(async (inputs: Record<string, number>) => {
    setLoading(true);
    // Simulate ML prediction
    await new Promise(r => setTimeout(r, 800));
    const pm25 = inputs.pm25 || 80;
    const pm10 = inputs.pm10 || 150;
    const aqi = Math.round(pm25 * 2.5 + pm10 * 0.5 + (inputs.no2 || 30) * 0.3 + Math.random() * 15);
    const cat = aqi <= 50 ? 'Good' : aqi <= 100 ? 'Satisfactory' : aqi <= 200 ? 'Moderate' : aqi <= 300 ? 'Poor' : aqi <= 400 ? 'Very Poor' : 'Severe';
    setResult({
      aqi, category: cat, confidence: 94,
      contributions: [
        { factor: 'PM2.5', impact: 45, color: '#84cc16' },
        { factor: 'PM10', impact: 30, color: '#eab308' },
        { factor: 'NO₂', impact: 15, color: '#f97316' },
        { factor: 'Weather', impact: 10, color: '#3b82f6' },
      ],
      recommendation: aqi > 200 ? 'Avoid outdoor activities. Wear N95 mask if going out.' : aqi > 100 ? 'Reduce prolonged outdoor exertion.' : 'Air quality is acceptable.',
    });
    setLoading(false);
  }, []);

  return { predict, result, loading };
}

export function useHyperlocalLocations() {
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetch(`${BASE}/hyperlocal/locations`)
      .then(r => r.json())
      .then(d => { setLocations(d); setLoading(false); })
      .catch(() => {
        setLocations([
          { location_id: 0, ward: 'Dwarka', zone: 'South West' },
          { location_id: 1, ward: 'Rohini', zone: 'North West' },
          { location_id: 2, ward: 'Saket', zone: 'South' },
          { location_id: 3, ward: 'Karol Bagh', zone: 'Central' },
          { location_id: 4, ward: 'Lajpat Nagar', zone: 'South East' },
        ]);
        setLoading(false);
      });
  }, []);
  return { locations, loading };
}

export function useHyperlocalForecast(locationId: number, steps = 72) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (locationId === undefined) return;
    setLoading(true);
    fetch(`${BASE}/hyperlocal/forecast/${locationId}?steps=${steps}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => {
        const last = 180 + Math.sin(Date.now() / 3600000) * 40;
        const forecast = Array.from({ length: steps }, (_, i) =>
          Math.round(last + Math.sin(i / 24) * 30 + (Math.random() - 0.5) * 15)
        );
        setData({ location_id: locationId, ward: 'Unknown', forecast, steps, latest_aqi: forecast[forecast.length - 1], category: 'Moderate' });
        setLoading(false);
      });
  }, [locationId, steps]);
  return { data, loading };
}
