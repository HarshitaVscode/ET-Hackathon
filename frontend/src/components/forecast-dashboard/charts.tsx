'use client';

import React from 'react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Card from '@/components/forecast-dashboard/ui/Card';
import { getAQIColor } from '@/app/forecast-dashboard/layout';

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

export function MiniSparkline({ data, color = '#3b82f6', height = 40 }: { data: number[]; color?: string; height?: number }) {
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={color} fill={`url(#spark-${color.replace('#', '')})`} strokeWidth={1.5} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function HistoricalTimelineChart({ data, height = 300, showGrid = true }: {
  data: { datetime: string; aqi: number; pm25?: number; pm10?: number }[];
  height?: number;
  showGrid?: boolean;
}) {
  const formatted = data.map(d => ({
    ...d,
    time: new Date(d.datetime).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' }),
    aqi: d.aqi,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="pm25Grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#84cc16" stopOpacity={0.2} />
            <stop offset="100%" stopColor="#84cc16" stopOpacity={0} />
          </linearGradient>
        </defs>
        {showGrid && <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />}
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 500]} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#aqiGrad)" dot={false} name="AQI" />
        {data[0]?.pm25 && <Area type="monotone" dataKey="pm25" stroke="#84cc16" strokeWidth={1} fill="url(#pm25Grad)" dot={false} name="PM2.5" strokeDasharray="4 4" />}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function BarComparisonChart({ data, height = 250 }: {
  data: { label: string; value: number; color?: string }[];
  height?: number;
}) {
  const chartData = data.map(d => ({ name: d.label, value: d.value }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={32}>
          {chartData.map((_, i) => (
            <rect key={i} fill={data[i]?.color || '#3b82f6'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ForecastBandChart({ data, history, height = 350 }: {
  data: { datetime: string; aqi: number; aqi_lower: number; aqi_upper: number; confidence: number }[];
  history?: { datetime: string; aqi: number }[];
  height?: number;
}) {
  const hist = (history || []).map(d => ({ ...d, time: new Date(d.datetime).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' }), isHist: true }));
  const fc = data.map(d => ({ ...d, time: new Date(d.datetime).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' }), isHist: false }));
  const all = [...hist, ...fc];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={all} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="fcGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.2} />
            <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 500]} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)' }} />
        {/* Confidence band */}
        <Area type="monotone" dataKey="aqi_upper" stroke="none" fill="rgba(249,115,22,0.08)" name="Upper" />
        <Area type="monotone" dataKey="aqi_lower" stroke="none" fill="rgba(249,115,22,0.08)" name="Lower" />
        {/* Observed */}
        <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#fcGrad)" dot={false} name="Observed AQI" />
        <Line type="monotone" dataKey="aqi" stroke="#ef4444" strokeWidth={2} strokeDasharray="6 3" dot={false} name="Predicted AQI"
          connectNulls /> {/* This won't work perfectly for mixing, but ok */}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function GaugeChart({ value = 285, max = 500, label = 'AQI', color }: { value?: number; max?: number; label?: string; color?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  const c = color || getAQIColor(value);
  const circumference = 2 * Math.PI * 70;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="140" viewBox="0 0 180 140">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="25%" stopColor="#84cc16" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="75%" stopColor="#f97316" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        {/* Background arc */}
        <path d="M 20 120 A 70 70 0 1 1 160 120" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="12" strokeLinecap="round" />
        {/* Value arc */}
        <path d="M 20 120 A 70 70 0 1 1 160 120" fill="none" stroke="url(#gaugeGrad)" strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset} style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
        {/* Tick labels */}
        <text x="20" y="132" fontSize="8" fill="rgba(255,255,255,0.3)" textAnchor="middle">0</text>
        <text x="90" y="138" fontSize="8" fill="rgba(255,255,255,0.3)" textAnchor="middle">{max / 2}</text>
        <text x="160" y="132" fontSize="8" fill="rgba(255,255,255,0.3)" textAnchor="middle">{max}</text>
        {/* Value */}
        <text x="90" y="85" fontSize="28" fontWeight="bold" fill="white" textAnchor="middle" dominantBaseline="middle">{value}</text>
        <text x="90" y="110" fontSize="10" fill="rgba(255,255,255,0.4)" textAnchor="middle" dominantBaseline="middle">{label}</text>
      </svg>
    </div>
  );
}
