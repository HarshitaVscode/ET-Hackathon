'use client'

import { AQITrendChart } from '@/components/charts/AQITrendChart'
import { SourceDonut } from '@/components/charts/SourceDonut'

export function AnalyticsView() {
  return (
    <div className="space-y-6">
      <div className="mb-2">
        <h2 className="text-lg font-semibold">Analytics</h2>
        <p className="text-xs text-gray-500 mt-1">Deep dive into air quality trends and source contributions</p>
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7 space-y-5">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-vayu-400" />
                <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">72-Hour Forecast Trend</h3>
              </div>
              <div className="flex gap-1">
                {['1H', '6H', '24H', '72H'].map((t) => (
                  <button key={t} className={`px-2 py-1 text-[10px] rounded-md ${t === '72H' ? 'bg-vayu-600/20 text-vayu-400' : 'text-gray-500 hover:text-gray-300'}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <AQITrendChart />
          </div>
          <div className="grid grid-cols-2 gap-5">
            <div className="card">
              <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Peak AQI Hours</h3>
              <div className="space-y-2">
                {[
                  { time: '08:00', aqi: 310, change: '+12%' },
                  { time: '12:00', aqi: 285, change: '-8%' },
                  { time: '18:00', aqi: 380, change: '+33%' },
                  { time: '22:00', aqi: 340, change: '-11%' },
                ].map((h) => (
                  <div key={h.time} className="flex items-center justify-between py-1.5 border-b border-gray-800/40 last:border-0">
                    <span className="text-xs text-gray-400">{h.time}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-200">{h.aqi}</span>
                      <span className={`text-[10px] ${h.change.startsWith('+') ? 'text-red-400' : 'text-green-400'}`}>{h.change}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Model Performance</h3>
              <div className="space-y-3">
                {[
                  { model: 'GraphCast', mae: '12.4', r2: '0.89' },
                  { model: 'TFT', mae: '15.8', r2: '0.82' },
                  { model: 'Ensemble', mae: '11.2', r2: '0.91' },
                ].map((m) => (
                  <div key={m.model} className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">{m.model}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-gray-500">MAE: {m.mae}</span>
                      <span className="text-[10px] text-green-400">R²: {m.r2}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-5 space-y-5">
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Source Contribution Trend</h3>
            <SourceDonut />
          </div>
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Forecast Accuracy</h3>
            <div className="space-y-3">
              {[
                { label: '24h ahead', accuracy: 92, color: 'bg-emerald-500' },
                { label: '48h ahead', accuracy: 78, color: 'bg-amber-500' },
                { label: '72h ahead', accuracy: 65, color: 'bg-orange-500' },
              ].map((f) => (
                <div key={f.label}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400">{f.label}</span>
                    <span className="text-xs font-medium text-gray-300">{f.accuracy}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${f.color}`} style={{ width: `${f.accuracy}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
