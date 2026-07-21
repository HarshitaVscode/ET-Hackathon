'use client';

import React from 'react';
import { getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';

export default function AQIScoreCard({ aqi = 285, size = 'lg' }: { aqi?: number; size?: 'sm' | 'lg' }) {
  const cat = getAQICategory(aqi);
  const color = getAQIColor(aqi);
  const pct = Math.min(100, (aqi / 500) * 100);

  const pollutants = [
    { label: 'PM2.5', value: Math.round(aqi * 0.45), max: 250, color: '#84cc16' },
    { label: 'PM10', value: Math.round(aqi * 0.85), max: 430, color: '#eab308' },
    { label: 'NO₂', value: Math.round(aqi * 0.16), max: 200, color: '#f97316' },
    { label: 'SO₂', value: Math.round(aqi * 0.05), max: 80, color: '#3b82f6' },
    { label: 'CO', value: Math.round(aqi * 0.025 * 10) / 10, max: 50, color: '#8b5cf6', unit: 'ppm' },
    { label: 'O₃', value: Math.round(aqi * 0.09), max: 180, color: '#06b6d4' },
    { label: 'NH₃', value: Math.round(aqi * 0.035), max: 100, color: '#ec4899' },
  ];

  const advice: Record<string, { title: string; desc: string; color: string }> = {
    Good: { title: 'Enjoy the outdoors', desc: 'Air quality is satisfactory with little or no health risk.', color: '#22c55e' },
    Satisfactory: { title: 'Acceptable air quality', desc: 'May cause minor health concerns for sensitive individuals.', color: '#84cc16' },
    Moderate: { title: 'Reduce prolonged exertion', desc: 'Unusually sensitive people should consider reducing outdoor activities.', color: '#eab308' },
    Poor: { title: 'Limit outdoor activities', desc: 'People with respiratory issues should avoid prolonged outdoor exertion.', color: '#f97316' },
    'Very Poor': { title: 'Avoid outdoor activities', desc: 'Wear N95 mask if going out. Keep windows closed.', color: '#ef4444' },
    Severe: { title: 'Health emergency', desc: 'Stay indoors. Use air purifier. Seek medical help if symptoms appear.', color: '#be123c' },
  };

  const ad = advice[cat] || advice.Moderate;

  return (
    <div className="rounded-2xl p-6 transition-all duration-500 hover:shadow-2xl"
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02))',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* AQI Number */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Current AQI</p>
          <div className="flex items-baseline gap-3">
            <span className="text-6xl font-bold tracking-tight transition-colors duration-700" style={{ color }}>{aqi}</span>
            <div>
              <span className="text-sm font-semibold px-2.5 py-0.5 rounded-full" style={{ background: `${color}20`, color, border: `1px solid ${color}30` }}>{cat}</span>
              <p className="text-[10px] text-gray-500 mt-1">Primary: PM2.5</p>
            </div>
          </div>
        </div>
        {/* AQI Bar */}
        <div className="hidden sm:block w-48">
          <div className="relative h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <div className="absolute inset-0 rounded-full" style={{
              background: 'linear-gradient(90deg, #22c55e, #84cc16 20%, #eab308 40%, #f97316 60%, #ef4444 80%, #be123c 100%)',
            }} />
            <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white shadow-lg transition-all duration-700 ease-out"
              style={{ left: `calc(${pct}% - 6px)`, boxShadow: `0 0 12px ${color}` }} />
          </div>
          <div className="flex justify-between mt-1 text-[9px] text-gray-600">
            <span>0</span><span>100</span><span>200</span><span>300</span><span>400</span><span>500</span>
          </div>
        </div>
      </div>

      {/* Pollutants */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {pollutants.map(p => {
          const pct2 = Math.min(100, (p.value / p.max) * 100);
          return (
            <div key={p.label} className="p-3 rounded-xl transition-all duration-200 hover:bg-white/5" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <p className="text-[10px] text-gray-500 mb-1">{p.label}</p>
              <p className="text-sm font-semibold text-gray-200">{p.value}{p.unit ? ` ${p.unit}` : ''}</p>
              <div className="mt-1.5 h-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct2}%`, background: p.color }} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Health Advisory */}
      <div className="rounded-xl p-4 transition-all duration-300" style={{ background: `${ad.color}10`, border: `1px solid ${ad.color}20` }}>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg" style={{ background: `${ad.color}20` }}>🫁</div>
          <div>
            <p className="text-sm font-semibold text-gray-200">{ad.title}</p>
            <p className="text-xs text-gray-400 mt-0.5">{ad.desc}</p>
          </div>
        </div>
      </div>

      {/* Standard */}
      <p className="text-[10px] text-gray-600 mt-3">AQI Standard: Indian NAQI • Updated just now</p>
    </div>
  );
}
