'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import { SegmentedControl } from '@/components/forecast-dashboard/ui/Tabs';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { HistoricalTimelineChart, BarComparisonChart, GaugeChart } from '@/components/forecast-dashboard/charts';
import { useHistoricalAQI } from '@/components/forecast-dashboard/useData';
import { getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-4 py-3 shadow-2xl" style={{ background: 'rgba(10,10,30,0.95)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color || p.stroke }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</p>
      ))}
    </div>
  );
};

const timeRanges = [
  { label: '24 Hours', value: '24h' },
  { label: '7 Days', value: '7d' },
  { label: '30 Days', value: '30d' },
  { label: '12 Months', value: '12m' },
];

const chartTypes = [
  { label: 'Line', value: 'line' },
  { label: 'Area', value: 'area' },
  { label: 'Bar', value: 'bar' },
];

const granulates = [
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
];

function aggregateData(data: any[], granularity: string) {
  if (granularity === 'hourly' || !data.length) return data;
  const by: Record<string, { sum: number; count: number; max: number; min: number }> = {};
  data.forEach(d => {
    const dt = new Date(d.datetime);
    const key = granularity === 'daily' ? dt.toISOString().slice(0, 10)
      : granularity === 'weekly' ? `${dt.getFullYear()}-W${Math.ceil(dt.getDate() / 7)}`
      : `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}`;
    if (!by[key]) by[key] = { sum: 0, count: 0, max: -Infinity, min: Infinity };
    by[key].sum += d.aqi;
    by[key].count++;
    by[key].max = Math.max(by[key].max, d.aqi);
    by[key].min = Math.min(by[key].min, d.aqi);
  });
  return Object.entries(by).map(([k, v]) => ({
    datetime: k,
    aqi: Math.round(v.sum / v.count),
    max: v.max,
    min: v.min,
  }));
}

export default function HistoricalPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [chartType, setChartType] = useState('area');
  const [granularity, setGranularity] = useState('hourly');
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const hoursMap: Record<string, number> = { '24h': 24, '7d': 168, '30d': 720, '12m': 8760 };
  const { data: rawData } = useHistoricalAQI({ hours: hoursMap[timeRange] || 168 });
  const data = useMemo(() => aggregateData(rawData, granularity), [rawData, granularity]);

  const aqiValues = data.map(d => d.aqi);
  const max = aqiValues.length ? Math.max(...aqiValues) : 0;
  const min = aqiValues.length ? Math.min(...aqiValues) : 0;
  const avg = aqiValues.length ? Math.round(aqiValues.reduce((a, b) => a + b, 0) / aqiValues.length) : 0;
  const sorted = [...aqiValues].sort((a, b) => a - b);
  const median = sorted.length ? sorted[Math.floor(sorted.length / 2)] : 0;

  // Distribution
  const dist = { Good: 0, Satisfactory: 0, Moderate: 0, Poor: 0, 'Very Poor': 0, Severe: 0 };
  aqiValues.forEach(v => {
    const c = getAQICategory(v);
    dist[c as keyof typeof dist]++;
  });
  const distData = Object.entries(dist).map(([k, v]) => ({ name: k, value: v }));
  const totalDist = aqiValues.length || 1;

  if (!mounted) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Historical AQI</h1>
          <p className="text-sm text-gray-500 mt-1">Analyze past air quality trends and patterns</p>
        </div>
        <Badge variant="info">{aqiValues.length} data points</Badge>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 animate-fadeIn">
        <SegmentedControl options={timeRanges.map(r => ({ label: r.label, value: r.value }))} value={timeRange} onChange={setTimeRange} />
        <SegmentedControl options={chartTypes} value={chartType} onChange={setChartType} />
        <SegmentedControl options={granulates} value={granularity} onChange={setGranularity} />
      </div>

      {/* Chart */}
      <div className="animate-fadeIn">
        <Card title="AQI Trend" subtitle={`${timeRange} • ${granularity} aggregation`} expandable>
          {chartType === 'bar' ? (
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                <XAxis dataKey="datetime" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 500]} />
                <Tooltip content={<CustomTooltip />} />
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                </defs>
                {chartType === 'area' ? (
                  <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#areaGrad)" dot={false} name="AQI" />
                ) : (
                  <>
                    <Area type="monotone" dataKey="max" stroke="#ef4444" strokeWidth={0} fill="none" name="Max" />
                    <Area type="monotone" dataKey="min" stroke="#22c55e" strokeWidth={0} fill="none" name="Min" />
                    <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#areaGrad)" dot={false} name="AQI" />
                    <Line type="monotone" dataKey="max" stroke="#ef4444" strokeWidth={1} strokeDasharray="3 3" dot={false} name="Max" />
                    <Line type="monotone" dataKey="min" stroke="#22c55e" strokeWidth={1} strokeDasharray="3 3" dot={false} name="Min" />
                  </>
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                <XAxis dataKey="datetime" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 500]} />
                <Tooltip content={<CustomTooltip />} />
                <defs>
                  <linearGradient id="areaGrad2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                </defs>
                <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#areaGrad2)" dot={false} name="AQI" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fadeIn">
        <Card title="Highest AQI">
          <div className="text-center">
            <p className="text-3xl font-bold" style={{ color: getAQIColor(max) }}>{max}</p>
            <p className="text-xs text-gray-500 mt-1">{getAQICategory(max)}</p>
          </div>
        </Card>
        <Card title="Lowest AQI">
          <div className="text-center">
            <p className="text-3xl font-bold" style={{ color: getAQIColor(min) }}>{min}</p>
            <p className="text-xs text-gray-500 mt-1">{getAQICategory(min)}</p>
          </div>
        </Card>
        <Card title="Average AQI">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-200">{avg}</p>
            <p className="text-xs text-gray-500 mt-1">{getAQICategory(avg)}</p>
          </div>
        </Card>
        <Card title="Median AQI">
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-200">{median}</p>
            <p className="text-xs text-gray-500 mt-1">{getAQICategory(median)}</p>
          </div>
        </Card>
      </div>

      {/* Distribution + Moving Average */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn">
        <Card title="AQI Distribution" subtitle="Category breakdown">
          <div className="space-y-3">
            {distData.map(d => (
              <div key={d.name} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-24">{d.name}</span>
                <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${(d.value / totalDist) * 100}%`, background: getAQIColor(
                    d.name === 'Good' ? 25 : d.name === 'Satisfactory' ? 75 : d.name === 'Moderate' ? 150 : d.name === 'Poor' ? 250 : d.name === 'Very Poor' ? 350 : 450
                  ) }} />
                </div>
                <span className="text-xs text-gray-300 font-medium w-12 text-right">{d.value}</span>
                <span className="text-xs text-gray-500 w-10 text-right">{Math.round((d.value / totalDist) * 100)}%</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Moving Average" subtitle="24-period rolling average">
          <HistoricalTimelineChart data={data.map((d, i) => {
            const window = 24;
            const slice = aqiValues.slice(Math.max(0, i - window + 1), i + 1);
            const ma = slice.length ? Math.round(slice.reduce((a, b) => a + b, 0) / slice.length) : d.aqi;
            return { ...d, aqi: ma };
          })} height={250} showGrid={true} />
        </Card>
      </div>
    </div>
  );
}
