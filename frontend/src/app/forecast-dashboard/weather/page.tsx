'use client';

import React, { useState, useEffect } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { useWeatherData } from '@/components/forecast-dashboard/useData';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-4 py-3 shadow-2xl" style={{ background: 'rgba(10,10,30,0.95)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color || p.stroke }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
};

export default function WeatherPage() {
  const { data: weather, loading } = useWeatherData();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  if (!mounted || loading) return <div className="h-96 flex items-center justify-center"><div className="w-6 h-6 border-2 border-blue-400/30 border-t-blue-400 rounded-full animate-spin" /></div>;

  const conditions = [
    { label: 'Temperature', value: `${weather?.temp}°C`, icon: '🌡️', detail: `Feels like ${(weather?.temp || 34) + 2}°C`, color: '#f97316' },
    { label: 'Humidity', value: `${weather?.humidity}%`, icon: '💧', detail: 'Moderate', color: '#3b82f6' },
    { label: 'Wind Speed', value: `${weather?.wind_speed} km/h`, icon: '💨', detail: `Direction: ${weather?.wind_dir}`, color: '#06b6d4' },
    { label: 'Wind Direction', value: weather?.wind_dir || 'NW', icon: '🧭', detail: '320°', color: '#8b5cf6' },
    { label: 'Pressure', value: `${weather?.pressure} hPa`, icon: '🔵', detail: 'Steady', color: '#6366f1' },
    { label: 'Rainfall', value: `${weather?.rainfall} mm`, icon: '🌧️', detail: 'Last 24h', color: '#22c55e' },
    { label: 'Visibility', value: `${weather?.visibility} km`, icon: '👁️', detail: 'Reduced due to haze', color: '#eab308' },
    { label: 'Cloud Cover', value: `${weather?.cloud_cover}%`, icon: '☁️', detail: 'Partly cloudy', color: '#6b7280' },
  ];

  const hourlyForecast = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}h`,
    temp: (weather?.temp || 34) + Math.sin(i / 24 * Math.PI * 2) * 4,
    humidity: (weather?.humidity || 62) + Math.sin(i / 12 * Math.PI) * 8,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Weather</h1>
          <p className="text-sm text-gray-500 mt-1">Current weather conditions and forecast for Delhi NCR</p>
        </div>
        <Badge variant="info">Updated just now</Badge>
      </div>

      {/* Current Conditions Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fadeIn">
        {conditions.map(c => (
          <Card key={c.label}>
            <div className="text-center">
              <span className="text-2xl">{c.icon}</span>
              <p className="text-xs text-gray-500 mt-1">{c.label}</p>
              <p className="text-xl font-bold text-gray-100 mt-0.5">{c.value}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">{c.detail}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Hourly Forecast */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn">
        <Card title="Temperature Forecast" subtitle="Next 24 hours">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hourlyForecast} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f97316" stopOpacity={0.3} /><stop offset="100%" stopColor="#f97316" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={['dataMin - 2', 'dataMax + 2']} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="temp" stroke="#f97316" strokeWidth={2} fill="url(#tempGrad)" dot={false} name="Temperature °C" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Humidity Forecast" subtitle="Next 24 hours">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={hourlyForecast} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="humGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="humidity" stroke="#3b82f6" strokeWidth={2} fill="url(#humGrad)" dot={false} name="Humidity %" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Weather Impact */}
      <div className="animate-fadeIn">
        <Card title="Weather Impact on AQI" subtitle="How weather affects pollution levels">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { factor: 'Wind Speed', impact: 'Moderate', detail: 'Current wind disperses pollutants at moderate rate', color: '#eab308' },
              { factor: 'Temperature', impact: 'High', detail: 'Higher temps increase photochemical smog formation', color: '#f97316' },
              { factor: 'Humidity', impact: 'Low', detail: 'Low humidity impact on PM concentrations', color: '#22c55e' },
              { factor: 'Rainfall', impact: 'Positive', detail: 'Rain helps wash out particulate matter', color: '#3b82f6' },
              { factor: 'Inversion', impact: 'None', detail: 'No thermal inversion layer detected', color: '#22c55e' },
              { factor: 'Visibility', impact: 'Moderate', detail: 'Reduced visibility indicates high PM levels', color: '#eab308' },
            ].map(w => (
              <div key={w.factor} className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                <p className="text-xs text-gray-500 font-medium">{w.factor}</p>
                <Badge variant={w.impact === 'High' ? 'danger' : w.impact === 'Moderate' ? 'warning' : 'success'} className="mt-1">{w.impact}</Badge>
                <p className="text-[10px] text-gray-500 mt-1.5">{w.detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
