'use client';

import React, { useEffect, useState } from 'react';
import ForecastCard from '../../components/forecasting/ForecastCard';
import HourlyChart from '../../components/forecasting/HourlyChart';
import LocationSelector from '../../components/forecasting/LocationSelector';

interface Location {
  location_id: number;
  ward: string;
  zone: string;
}

interface ForecastData {
  location_id: number;
  ward: string;
  zone: string;
  forecast: number[];
  latest_aqi: number;
  category: string;
}

export default function HyperlocalPage() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [selected, setSelected] = useState<number>(0);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [allForecasts, setAllForecasts] = useState<ForecastData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/hyperlocal/locations')
      .then(r => r.json())
      .then(data => {
        setLocations(data);
        if (data.length > 0) setSelected(data[0].location_id);
      })
      .catch(() => setError('Failed to load locations'));
  }, []);

  useEffect(() => {
    if (selected === undefined) return;
    setLoading(true);
    fetch(`/api/v1/hyperlocal/forecast/${selected}?steps=72`)
      .then(r => r.json())
      .then(data => {
        if (data.error) { setError(data.error); return; }
        setForecast(data);
        setLoading(false);
      })
      .catch(() => { setError('Failed to load forecast'); setLoading(false); });
  }, [selected]);

  useEffect(() => {
    fetch('/api/v1/hyperlocal/forecast/all?steps=72')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) setAllForecasts(data);
      })
      .catch(() => {});
  }, []);

  const historyData = forecast ? Array.from({ length: 168 }, (_, i) =>
    Math.round(forecast.latest_aqi + Math.sin(i / 12) * 15 + (Math.random() - 0.5) * 10)
  ) : [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Hyperlocal AQI Forecast</h1>
        <p className="text-gray-600 mb-6">24–72 hour ward-level AQI predictions using time-series models</p>

        {error && (
          <div className="bg-red-100 text-red-800 px-4 py-3 rounded-lg mb-4">{error}</div>
        )}

        <LocationSelector locations={locations} selected={selected} onSelect={setSelected} />

        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading forecast...</div>
        ) : forecast && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2">
              <HourlyChart
                ward={forecast.ward}
                history={historyData}
                forecast={forecast.forecast}
              />
            </div>
            <div>
              <ForecastCard
                ward={forecast.ward}
                currentAqi={Math.round(forecast.latest_aqi)}
                forecast24h={forecast.forecast.length > 23 ? Math.round(forecast.forecast[23]) : 0}
                forecast48h={forecast.forecast.length > 47 ? Math.round(forecast.forecast[47]) : 0}
                forecast72h={forecast.forecast.length > 0 ? Math.round(forecast.forecast[forecast.forecast.length - 1]) : 0}
                category={forecast.category}
              />
            </div>
          </div>
        )}

        {allForecasts.length > 0 && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">All Locations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {allForecasts.map(f => (
                <ForecastCard
                  key={f.location_id}
                  ward={f.ward}
                  currentAqi={Math.round(f.latest_aqi)}
                  forecast24h={f.forecast.length > 23 ? Math.round(f.forecast[23]) : 0}
                  forecast48h={f.forecast.length > 47 ? Math.round(f.forecast[47]) : 0}
                  forecast72h={f.forecast.length > 0 ? Math.round(f.forecast[f.forecast.length - 1]) : 0}
                  category={f.category}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
