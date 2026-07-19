'use client';

import React from 'react';

interface HourlyChartProps {
  ward: string;
  history: number[];
  forecast: number[];
}

const WIDTH = 600;
const HEIGHT = 200;
const PAD = { top: 20, right: 20, bottom: 30, left: 40 };

const aqiColor = (v: number) => {
  if (v <= 50) return '#22c55e';
  if (v <= 100) return '#84cc16';
  if (v <= 200) return '#eab308';
  if (v <= 300) return '#f97316';
  if (v <= 400) return '#ef4444';
  return '#be123c';
};

export default function HourlyChart({ ward, history, forecast }: HourlyChartProps) {
  const all = [...history, ...forecast];
  const mn = Math.min(...all);
  const mx = Math.max(...all);
  const range = mx - mn || 1;

  const plotW = WIDTH - PAD.left - PAD.right;
  const plotH = HEIGHT - PAD.top - PAD.bottom;

  const historyPath = history.map((v, i) => {
    const x = PAD.left + (i / Math.max(history.length - 1, 1)) * plotW;
    const y = PAD.top + plotH - ((v - mn) / range) * plotH;
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  const forecastPath = forecast.map((v, i) => {
    const x = PAD.left + ((history.length + i) / Math.max(all.length - 1, 1)) * plotW;
    const y = PAD.top + plotH - ((v - mn) / range) * plotH;
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  const gridLines = [0, 50, 100, 200, 300, 400].filter(v => v >= mn && v <= mx);

  return (
    <div className="bg-white rounded-xl p-4 shadow-md">
      <h3 className="text-lg font-bold text-gray-900 mb-2">{ward} - AQI Forecast</h3>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full h-auto">
        {gridLines.map(v => {
          const y = PAD.top + plotH - ((v - mn) / range) * plotH;
          return (
            <g key={v}>
              <line x1={PAD.left} y1={y} x2={WIDTH - PAD.right} y2={y} stroke="#e5e7eb" strokeWidth={1} />
              <text x={PAD.left - 5} y={y + 4} textAnchor="end" fontSize={10} fill="#6b7280">{v}</text>
            </g>
          );
        })}
        <line x1={PAD.left + (history.length / Math.max(all.length - 1, 1)) * plotW} y1={PAD.top}
              x2={PAD.left + (history.length / Math.max(all.length - 1, 1)) * plotW} y2={HEIGHT - PAD.bottom}
              stroke="#9ca3af" strokeWidth={1} strokeDasharray="4,4" />
        <path d={historyPath} fill="none" stroke="#3b82f6" strokeWidth={2} />
        <path d={forecastPath} fill="none" stroke="#ef4444" strokeWidth={2} strokeDasharray="6,3" />
        <text x={WIDTH / 2} y={HEIGHT - 2} textAnchor="middle" fontSize={11} fill="#6b7280">Hours</text>
      </svg>
      <div className="flex gap-4 mt-2 text-xs text-gray-600">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-500 inline-block" /> History</span>
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500 inline-block" /> Forecast</span>
      </div>
    </div>
  );
}
