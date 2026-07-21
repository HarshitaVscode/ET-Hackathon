'use client';

import React, { useState, useEffect, useRef } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';
import { useWeatherData, useSourceAttribution } from '@/components/forecast-dashboard/useData';

// Grid cell data
const zones = [
  { id: 0, name: 'Dwarka', aqi: 215, lat: 28.59, lng: 77.05 },
  { id: 1, name: 'Rohini', aqi: 248, lat: 28.73, lng: 77.12 },
  { id: 2, name: 'Saket', aqi: 178, lat: 28.52, lng: 77.22 },
  { id: 3, name: 'Karol Bagh', aqi: 265, lat: 28.65, lng: 77.19 },
  { id: 4, name: 'Lajpat Nagar', aqi: 195, lat: 28.57, lng: 77.24 },
  { id: 5, name: 'Connaught Place', aqi: 290, lat: 28.63, lng: 77.22 },
  { id: 6, name: 'Chandni Chowk', aqi: 310, lat: 28.66, lng: 77.23 },
  { id: 7, name: 'Hauz Khas', aqi: 160, lat: 28.55, lng: 77.20 },
  { id: 8, name: 'Pitampura', aqi: 230, lat: 28.70, lng: 77.13 },
  { id: 9, name: 'Vasant Kunj', aqi: 185, lat: 28.54, lng: 77.15 },
];

const sources = [
  { name: 'Industrial Zone', type: 'industrial', lat: 28.62, lng: 77.08, impact: 'High' },
  { name: 'Thermal Plant', type: 'industrial', lat: 28.58, lng: 77.03, impact: 'Very High' },
  { name: 'Bus Terminal', type: 'traffic', lat: 28.65, lng: 77.21, impact: 'High' },
  { name: 'Construction Site', type: 'dust', lat: 28.56, lng: 77.18, impact: 'Medium' },
  { name: 'Fire Event', type: 'fire', lat: 28.67, lng: 77.25, impact: 'Critical' },
  { name: 'Monitoring Station', type: 'station', lat: 28.61, lng: 77.16, impact: '-' },
];

export default function MapPage() {
  const [selectedZone, setSelectedZone] = useState<typeof zones[0] | null>(null);
  const [timeSlider, setTimeSlider] = useState(0);
  const [mounted, setMounted] = useState(false);
  const { data: weather } = useWeatherData();
  const { data: sourcesData } = useSourceAttribution();

  useEffect(() => { setMounted(true); }, []);

  if (!mounted) return null;

  const viewBox = "0 0 800 600";

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Pollution Map</h1>
          <p className="text-sm text-gray-500 mt-1">Interactive hyperlocal AQI visualization with 1 km grid</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="warning">Live</Badge>
          <Badge variant="info">1 km Grid</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Map */}
        <div className="lg:col-span-3 animate-fadeIn">
          <Card title="Delhi NCR - AQI Heatmap" subtitle="Hyperlocal 1 km grid • Wind: {weather?.wind_speed || 12} km/h {weather?.wind_dir || 'NW'}"
            expandable>
            <svg viewBox={viewBox} className="w-full h-auto rounded-xl" style={{ background: 'linear-gradient(180deg, #0a0a2e 0%, #1a1a3e 100%)' }}>
              {/* Grid cells */}
              {zones.map((z, i) => {
                const cx = 100 + (z.lng - 77.0) * 200;
                const cy = 100 + (28.9 - z.lat) * 200;
                const color = getAQIColor(z.aqi);
                const selected = selectedZone?.id === z.id;
                return (
                  <g key={z.id} onClick={() => setSelectedZone(z)} className="cursor-pointer transition-all duration-200">
                    <rect x={cx - 25} y={cy - 25} width={50} height={50} rx={6}
                      fill={`${color}40`} stroke={selected ? 'white' : `${color}60`} strokeWidth={selected ? 2 : 1}
                      style={{ filter: selected ? `drop-shadow(0 0 12px ${color}60)` : 'none' }}
                    />
                    <text x={cx} y={cy - 8} textAnchor="middle" fill="rgba(255,255,255,0.7)" fontSize="8" fontWeight="bold">{z.name}</text>
                    <text x={cx} y={cy + 10} textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">{z.aqi}</text>
                  </g>
                );
              })}

              {/* Sources */}
              {sources.map((s, i) => {
                const cx = 100 + (s.lng - 77.0) * 200;
                const cy = 100 + (28.9 - s.lat) * 200;
                const icons: Record<string, string> = { industrial: '🏭', traffic: '🚗', dust: '🏗️', fire: '🔥', station: '📡' };
                return (
                  <g key={i}>
                    <text x={cx} y={cy} textAnchor="middle" fontSize="16" cursor="pointer">
                      {icons[s.type] || '📍'}
                    </text>
                    <text x={cx} y={cy + 18} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="6">{s.name}</text>
                  </g>
                );
              })}

              {/* Wind indicator */}
              <g transform={`translate(700, 80)`}>
                <text x="0" y="-10" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="8">Wind</text>
                <line x1="0" y1="0" x2="-20" y2="-15" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
                <text x="0" y="15" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7">{weather?.wind_dir || 'NW'}</text>
              </g>

              {/* Legend */}
              <g transform="translate(20, 520)">
                <text x="0" y="0" fill="rgba(255,255,255,0.3)" fontSize="8">AQI</text>
                {[50, 100, 200, 300, 400].map((v, i) => (
                  <rect key={i} x={i * 35 + 5} y="-12" width="30" height="8" rx="2" fill={getAQIColor(v + 1)} />
                ))}
                <text x="5" y="-20" fill="rgba(255,255,255,0.2)" fontSize="7">Good</text>
                <text x="180" y="-20" fill="rgba(255,255,255,0.2)" fontSize="7">Severe</text>
              </g>

              {/* Title */}
              <text x="20" y="25" fill="rgba(255,255,255,0.5)" fontSize="9">Satellite • Hybrid • Updated: just now</text>
            </svg>

            {/* Time Slider */}
            <div className="flex items-center gap-3 mt-4">
              <span className="text-[10px] text-gray-500">Now</span>
              <input type="range" min={-48} max={72} value={timeSlider} onChange={e => setTimeSlider(Number(e.target.value))}
                className="flex-1 h-1 rounded-full appearance-none cursor-pointer"
                style={{ background: 'rgba(255,255,255,0.1)' }} />
              <span className="text-[10px] text-gray-500">{timeSlider > 0 ? `+${timeSlider}h` : timeSlider < 0 ? `${timeSlider}h` : 'Now'}</span>
            </div>
          </Card>
        </div>

        {/* Side Panel */}
        <div className="space-y-4 animate-fadeIn">
          {/* Selected Zone Detail */}
          <Card title={selectedZone ? selectedZone.name : 'Zone Detail'} subtitle={selectedZone ? `Grid Cell • 1 km²` : 'Click a grid cell'}>
            {selectedZone ? (
              <div className="space-y-3">
                <div className="text-center">
                  <p className="text-4xl font-bold" style={{ color: getAQIColor(selectedZone.aqi) }}>{selectedZone.aqi}</p>
                  <Badge variant={selectedZone.aqi > 200 ? 'danger' : selectedZone.aqi > 100 ? 'warning' : 'success'}>{getAQICategory(selectedZone.aqi)}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <p className="text-gray-500">24h</p>
                    <p className="text-gray-200 font-medium">{Math.round(selectedZone.aqi + 12)}</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <p className="text-gray-500">48h</p>
                    <p className="text-gray-200 font-medium">{Math.round(selectedZone.aqi + 25)}</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <p className="text-gray-500">72h</p>
                    <p className="text-gray-200 font-medium">{Math.round(selectedZone.aqi + 35)}</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                    <p className="text-gray-500">Confidence</p>
                    <p className="text-green-400 font-medium">87%</p>
                  </div>
                </div>
                <div className="p-3 rounded-lg text-xs" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <p className="text-gray-500">Dominant Pollutant</p>
                  <p className="text-gray-200 font-medium">PM2.5 • {Math.round(selectedZone.aqi * 0.45)} µg/m³</p>
                </div>
                <div className="p-3 rounded-lg text-xs" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <p className="text-gray-500">Health Category</p>
                  <p className="text-gray-200 font-medium">{selectedZone.aqi > 200 ? 'Unhealthy - Limit outdoor activities' : 'Moderate - Caution advised'}</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center py-8 text-gray-500">
                <span className="text-3xl mb-2">👆</span>
                <p className="text-xs">Select a grid cell to view details</p>
              </div>
            )}
          </Card>

          {/* Weather Overlay */}
          <Card title="Weather Layers" subtitle="Current conditions">
            <div className="space-y-2 text-xs">
              {[
                { label: 'Wind Direction', value: `${weather?.wind_dir || 'NW'} (320°)` },
                { label: 'Wind Speed', value: `${weather?.wind_speed || 12} km/h` },
                { label: 'Pollution Dispersion', value: weather?.wind_speed && weather.wind_speed > 10 ? 'Favorable - pollutants dispersing' : 'Stagnant - accumulation likely' },
                { label: 'Inversion Layer', value: weather?.temp && weather.temp > 30 ? 'No inversion' : 'Weak inversion possible' },
              ].map((l, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <span className="text-gray-500">{l.label}</span>
                  <span className="text-gray-200 text-right max-w-[160px]">{l.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
