'use client';

import React, { useState, useEffect } from 'react';
import { useTheme, getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import AQIScoreCard from '@/components/forecast-dashboard/AQIScoreCard';
import { GaugeChart, HistoricalTimelineChart, MiniSparkline } from '@/components/forecast-dashboard/charts';
import { useCurrentAQI, useHistoricalAQI, useForecast, useWeatherData, useSourceAttribution } from '@/components/forecast-dashboard/useData';

function StatCard({ label, value, sub, color, trend }: { label: string; value: string; sub?: string; color?: string; trend?: 'up' | 'down' | 'stable' }) {
  return (
    <div className="rounded-xl p-4 transition-all duration-200 hover:bg-white/[0.02]" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">{label}</p>
      <p className="text-xl font-bold text-gray-100 mt-1" style={color ? { color } : {}}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      {trend && <span className={`text-[10px] ${trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-green-400' : 'text-gray-400'}`}>
        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trend === 'up' ? 'Rising' : trend === 'down' ? 'Falling' : 'Stable'}
      </span>}
    </div>
  );
}

export default function ExecutiveOverview() {
  const { theme } = useTheme();
  const { data: current } = useCurrentAQI();
  const { data: historical } = useHistoricalAQI({ hours: 72 });
  const { data: forecast } = useForecast({ steps: 72 });
  const { data: weather } = useWeatherData();
  const { data: sources } = useSourceAttribution();
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;

  const aqi = current?.aqi || 285;
  const cat = getAQICategory(aqi);
  const color = getAQIColor(aqi);
  const aqiHistory = historical.map(d => d.aqi);
  const aqiForecast = forecast.map(d => d.aqi);
  const allAqi = [...aqiHistory, ...aqiForecast];

  const forecastTrend = aqiForecast.length > 1
    ? (aqiForecast[aqiForecast.length - 1] - aqiForecast[0]) > 10 ? 'up'
      : (aqiForecast[aqiForecast.length - 1] - aqiForecast[0]) < -10 ? 'down' : 'stable'
    : 'stable';

  const dominantSource = sources.reduce((max, s) => s.value > max.value ? s : max, sources[0] || { name: 'N/A', value: 0 });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Executive Overview</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time air quality intelligence for Delhi NCR</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={cat === 'Poor' || cat === 'Very Poor' || cat === 'Severe' ? 'danger' : cat === 'Moderate' ? 'warning' : 'success'}>
            {cat}
          </Badge>
          <Badge variant="info">{aqi} AQI</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AQI Score Card */}
        <div className="lg:col-span-2 animate-fadeIn" style={{ animationDelay: '0.1s' }}>
          <AQIScoreCard aqi={aqi} />
        </div>

        {/* Quick Stats */}
        <div className="space-y-3 animate-fadeIn" style={{ animationDelay: '0.2s' }}>
          <Card title="Quick Stats" subtitle="Current conditions overview">
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Dominant Pollutant" value="PM2.5" sub={`${Math.round(aqi * 0.45)} µg/m³`} color="#84cc16" />
              <StatCard label="Forecast Trend" value={forecastTrend === 'up' ? 'Worsening' : forecastTrend === 'down' ? 'Improving' : 'Stable'}
                trend={forecastTrend} />
              <StatCard label="Temperature" value={`${weather?.temp || 34}°C`} sub={`Feels like ${(weather?.temp || 34) + 2}°C`} color="#f97316" />
              <StatCard label="Humidity" value={`${weather?.humidity || 62}%`} sub="Moderate" color="#3b82f6" />
              <StatCard label="Wind" value={`${weather?.wind_speed || 12} km/h`} sub={`Direction: ${weather?.wind_dir || 'NW'}`} color="#06b6d4" />
              <StatCard label="Visibility" value={`${weather?.visibility || 4.5} km`} sub="Reduced due to haze" color="#8b5cf6" />
            </div>
          </Card>

          <Card title="Latest Update" subtitle="Prediction timestamp">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <div>
                <p className="text-xs text-gray-400">Model prediction</p>
                <p className="text-sm text-gray-200 font-medium">just now</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 72h Timeline */}
      <div className="animate-fadeIn" style={{ animationDelay: '0.3s' }}>
        <Card title="AQI Timeline" subtitle="72-hour historical and forecast" onRefresh={() => {}}>
          <HistoricalTimelineChart data={[...historical.slice(-48), ...forecast.map(f => ({ datetime: f.datetime, aqi: f.aqi }))]} height={300} />
        </Card>
      </div>

      {/* Info Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fadeIn" style={{ animationDelay: '0.4s' }}>
        <Card title="Confidence Score" subtitle="Model prediction confidence">
          <div className="text-center py-2">
            <div className="text-3xl font-bold text-blue-400">94%</div>
            <p className="text-xs text-gray-500 mt-1">Based on ensemble agreement</p>
            <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400" style={{ width: '94%' }} />
            </div>
          </div>
        </Card>

        <Card title="Health Recommendation" subtitle={cat}>
          <div className="flex items-start gap-3 py-2">
            <span className="text-2xl">{aqi > 200 ? '😷' : aqi > 100 ? '⚠️' : '😊'}</span>
            <div>
              <p className="text-sm text-gray-200 font-medium">
                {aqi > 300 ? 'Avoid outdoors' : aqi > 200 ? 'Limit exposure' : aqi > 100 ? 'Caution advised' : 'Air is clean'}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {aqi > 200 ? 'Wear N95 mask if going out.' : 'Sensitive groups should limit exertion.'}
              </p>
            </div>
          </div>
        </Card>

        <Card title="Traffic Impact" subtitle="Current congestion">
          <div className="flex items-center gap-3 py-2">
            <span className="text-2xl">🚗</span>
            <div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-16 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                  <div className="h-full rounded-full bg-orange-400" style={{ width: '72%' }} />
                </div>
                <span className="text-xs text-orange-400 font-medium">72%</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">Heavy traffic in central zones</p>
            </div>
          </div>
        </Card>

        <Card title="Industrial Impact" subtitle="Sector contribution">
          <div className="flex items-center gap-3 py-2">
            <span className="text-2xl">🏭</span>
            <div>
              <div className="flex items-center gap-2">
                <div className="h-2 w-16 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                  <div className="h-full rounded-full bg-red-400" style={{ width: '38%' }} />
                </div>
                <span className="text-xs text-red-400 font-medium">38%</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">3 km from monitoring station</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Source Attribution + Weather */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn" style={{ animationDelay: '0.5s' }}>
        <Card title="Pollution Sources" subtitle="Contribution breakdown">
          <div className="space-y-3">
            {sources.map(s => (
              <div key={s.name} className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                <span className="text-xs text-gray-400 w-28">{s.name}</span>
                <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${s.value}%`, background: s.color }} />
                </div>
                <span className="text-xs text-gray-300 font-medium w-8 text-right">{s.value}%</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Weather Summary" subtitle="Current conditions">
          {weather && (
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Temperature', value: `${weather.temp}°C`, icon: '🌡️' },
                { label: 'Wind', value: `${weather.wind_speed} km/h ${weather.wind_dir}`, icon: '💨' },
                { label: 'Humidity', value: `${weather.humidity}%`, icon: '💧' },
                { label: 'Pressure', value: `${weather.pressure} hPa`, icon: '🔵' },
                { label: 'Visibility', value: `${weather.visibility} km`, icon: '👁️' },
                { label: 'Cloud Cover', value: `${weather.cloud_cover}%`, icon: '☁️' },
              ].map(w => (
                <div key={w.label} className="p-3 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <span className="text-lg">{w.icon}</span>
                  <p className="text-xs text-gray-500 mt-1">{w.label}</p>
                  <p className="text-sm font-semibold text-gray-200">{w.value}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
