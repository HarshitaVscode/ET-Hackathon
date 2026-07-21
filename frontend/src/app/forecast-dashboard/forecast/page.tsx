'use client';

import React, { useState, useEffect } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { SegmentedControl } from '@/components/forecast-dashboard/ui/Tabs';
import { ForecastBandChart } from '@/components/forecast-dashboard/charts';
import { useHistoricalAQI, useForecast } from '@/components/forecast-dashboard/useData';
import { getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

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

const horizons = [
  { label: '24 Hours', value: 24 },
  { label: '48 Hours', value: 48 },
  { label: '72 Hours', value: 72 },
];

export default function ForecastPage() {
  const [horizon, setHorizon] = useState(72);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const { data: history } = useHistoricalAQI({ hours: 72 });
  const { data: forecast } = useForecast({ steps: 72 });

  const slicedForecast = forecast.slice(0, horizon);
  const lastHist = history.length > 0 ? history[history.length - 1].aqi : 200;

  const combined = [
    ...history.slice(-48).map(d => ({ ...d, type: 'Observed' })),
    ...slicedForecast.map(d => ({ ...d, type: 'Predicted' })),
  ];

  if (!mounted) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Forecast Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">AI-powered hyperlocal air quality predictions</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info">Ensemble Model</Badge>
          <Badge variant="warning">Live</Badge>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 animate-fadeIn">
        <SegmentedControl options={horizons} value={String(horizon)} onChange={v => setHorizon(Number(v))} />
      </div>

      {/* Combined Timeline */}
      <div className="animate-fadeIn">
        <Card title="Combined Timeline" subtitle="Observed → Predicted AQI" expandable>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={combined} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="obsGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} /><stop offset="100%" stopColor="#ef4444" stopOpacity={0} /></linearGradient>
                <linearGradient id="upperGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#f97316" stopOpacity={0.1} /><stop offset="100%" stopColor="#f97316" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="datetime" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false}
                tickFormatter={(v) => new Date(v).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' })}
                interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 500]} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)' }} />
              {/* Confidence band */}
              <Area type="monotone" dataKey="aqi_upper" stroke="none" fill="url(#upperGrad)" name="Upper Bound" />
              <Area type="monotone" dataKey="aqi_lower" stroke="none" fill="url(#upperGrad)" name="Lower Bound" />
              <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fill="url(#obsGrad)" dot={false} name="Observed AQI" />
              {/* Predicted overlay */}
              {combined.filter(d => d.type === 'Predicted').length > 0 && (
                <Area type="monotone" dataKey="aqi" stroke="#ef4444" strokeWidth={2.5} fill="url(#predGrad)" dot={false} strokeDasharray="8 4" name="Predicted AQI"
                  connectNulls />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Forecast Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fadeIn">
        {[24, 48, 72].map(h => {
          const f = forecast.slice(0, h);
          const avg = f.length ? Math.round(f.reduce((a, b) => a.aqi + b.aqi, 0) / f.length) : 0;
          const maxF = f.length ? Math.max(...f.map(d => d.aqi)) : 0;
          const minF = f.length ? Math.min(...f.map(d => d.aqi)) : 0;
          const conf = f.length ? Math.round(f.reduce((a, b) => a + b.confidence, 0) / f.length) : 0;
          return (
            <Card key={h} title={`${h}-Hour Forecast`}>
              <div className="text-center">
                <p className="text-3xl font-bold text-gray-100">{avg}</p>
                <p className="text-xs text-gray-500 mt-1">Average AQI • {getAQICategory(avg)}</p>
                <div className="flex justify-center gap-4 mt-3 text-xs">
                  <span className="text-red-400">H {maxF}</span>
                  <span className="text-green-400">L {minF}</span>
                  <span className="text-blue-400">{conf}% conf</span>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Hourly Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fadeIn">
        <Card title="Hourly Forecast" subtitle="Per-hour AQI predictions">
          <div className="space-y-1 max-h-80 overflow-y-auto scrollbar-thin">
            {slicedForecast.map((f, i) => (
              <div key={i} className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-white/[0.02] transition-colors">
                <span className="text-xs text-gray-500 w-16">
                  {new Date(f.datetime).toLocaleDateString('en-IN', { hour: '2-digit', day: 'numeric', month: 'short' })}
                </span>
                <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <div className="h-full rounded-full transition-all" style={{ width: `${(f.aqi / 500) * 100}%`, background: getAQIColor(f.aqi) }} />
                </div>
                <span className="text-xs font-semibold text-gray-300 w-10 text-right">{f.aqi}</span>
                <span className="text-[10px] text-gray-500 w-12 text-right">{f.confidence}%</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Confidence & Uncertainty" subtitle="Prediction reliability over time">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={slicedForecast} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} /><stop offset="100%" stopColor="#22c55e" stopOpacity={0} /></linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="datetime" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `${new Date(v).getHours()}h`} interval={5} />
              <YAxis yAxisId="left" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Area yAxisId="left" type="monotone" dataKey="confidence" stroke="#22c55e" strokeWidth={2} fill="url(#confGrad)" dot={false} name="Confidence %" />
              <Area yAxisId="left" type="monotone" dataKey="aqi_upper" stroke="#f97316" strokeWidth={1} strokeDasharray="3 3" dot={false} name="Upper Bound" fill="none" />
              <Area yAxisId="left" type="monotone" dataKey="aqi_lower" stroke="#3b82f6" strokeWidth={1} strokeDasharray="3 3" dot={false} name="Lower Bound" fill="none" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Export */}
      <div className="flex gap-3 animate-fadeIn">
        <button className="px-4 py-2 rounded-xl text-xs font-medium text-gray-300 transition-all duration-200 hover:text-white"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
          Download PNG
        </button>
        <button className="px-4 py-2 rounded-xl text-xs font-medium text-gray-300 transition-all duration-200 hover:text-white"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
          Export CSV
        </button>
        <button className="px-4 py-2 rounded-xl text-xs font-medium text-gray-300 transition-all duration-200 hover:text-white"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
          Export PDF
        </button>
      </div>
    </div>
  );
}
