'use client'

import { useEffect, useState } from 'react'

const data = [
  { hour: '00', aqi: 245 },
  { hour: '03', aqi: 230 },
  { hour: '06', aqi: 260 },
  { hour: '09', aqi: 310 },
  { hour: '12', aqi: 285 },
  { hour: '15', aqi: 340 },
  { hour: '18', aqi: 380 },
  { hour: '21', aqi: 320 },
]

const forecast = [
  { hour: '00', aqi: 295 },
  { hour: '+6h', aqi: 330 },
  { hour: '+12h', aqi: 380 },
  { hour: '+24h', aqi: 350 },
  { hour: '+48h', aqi: 310 },
  { hour: '+72h', aqi: 275 },
]

const maxAqi = 450
const pad = { top: 20, right: 20, bottom: 30, left: 40 }
const chartW = 320
const chartH = 140
const innerW = chartW - pad.left - pad.right
const innerH = chartH - pad.top - pad.bottom

const getPoint = (val: number, i: number, len: number) => ({
  x: pad.left + (i / (len - 1)) * innerW,
  y: pad.top + innerH - (val / maxAqi) * innerH,
})

const pathD = (pts: { x: number; y: number }[]) =>
  pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

const areaD = (pts: { x: number; y: number }[]) =>
  pathD(pts) + ` L ${pts[pts.length - 1].x} ${pad.top + innerH} L ${pts[0].x} ${pad.top + innerH} Z`

export function AQITrendChart() {
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 200)
    return () => clearTimeout(t)
  }, [])

  const histPoints = data.map((d, i) => getPoint(d.aqi, i, data.length))
  const forePoints = forecast.map((d, i) => getPoint(d.aqi, i, forecast.length))
  const dividerX = pad.left + ((data.length - 1) / (data.length + forecast.length - 1)) * innerW

  const aqiColor = (v: number) =>
    v > 400 ? '#ff0040' : v > 300 ? '#ff6b00' : v > 200 ? '#ffbb00' : v > 100 ? '#aadd00' : '#00e400'

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="w-1 h-4 rounded-full bg-gradient-to-b from-vayu-400 to-vayu-600" />
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">72-Hour Trend</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-[9px] text-gray-500">
            <span className="w-3 h-0.5 rounded bg-vayu-400" />
            History
          </span>
          <span className="flex items-center gap-1.5 text-[9px] text-gray-500">
            <span className="w-3 h-0.5 rounded bg-vayu-500/50" style={{ borderTop: '1px dashed rgba(56,189,248,0.5)', height: 0 }} />
            Forecast
          </span>
        </div>
      </div>

      <svg width="100%" height={chartH + 10} viewBox={`0 0 ${chartW} ${chartH}`} className="overflow-visible">
        {/* Grid lines */}
        {[0, 100, 200, 300, 400].map((v) => {
          const y = pad.top + innerH - (v / maxAqi) * innerH
          return (
            <g key={v}>
              <line x1={pad.left} y1={y} x2={pad.left + innerW} y2={y} stroke="#1f2937" strokeWidth={0.5} strokeDasharray="3,3" />
              <text x={pad.left - 6} y={y + 3} textAnchor="end" fill="#4b5563" fontSize="8" fontFamily="JetBrains Mono, monospace">{v}</text>
            </g>
          )
        })}

        {/* AQI zone backgrounds */}
        <defs>
          <linearGradient id="zonePoor" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="rgba(255,0,0,0.03)" /><stop offset="1" stopColor="rgba(255,0,0,0.08)" /></linearGradient>
          <linearGradient id="zoneHigh" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="rgba(255,126,0,0.03)" /><stop offset="1" stopColor="rgba(255,126,0,0.06)" /></linearGradient>
          <linearGradient id="zoneMod" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="rgba(255,255,0,0.02)" /><stop offset="1" stopColor="rgba(255,255,0,0.05)" /></linearGradient>
          <linearGradient id="areaHist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="rgba(56,189,248,0.25)" /><stop offset="1" stopColor="rgba(56,189,248,0.02)" /></linearGradient>
          <linearGradient id="areaFore" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="rgba(56,189,248,0.12)" /><stop offset="1" stopColor="rgba(56,189,248,0.01)" /></linearGradient>
          <filter id="glowLine"><feGaussianBlur stdDeviation="2" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>

        <rect x={pad.left} y={pad.top} width={innerW} height={(200 / maxAqi) * innerH} fill="url(#zoneMod)" />
        <rect x={pad.left} y={pad.top + (1 - 300 / maxAqi) * innerH} width={innerW} height={(100 / maxAqi) * innerH} fill="url(#zoneHigh)" />
        <rect x={pad.left} y={pad.top} width={innerW} height={(1 - 300 / maxAqi) * innerH} fill="url(#zonePoor)" />

        {/* History area fill */}
        <path d={areaD(histPoints)} fill="url(#areaHist)" opacity={animated ? 1 : 0} className="transition-opacity duration-700" />

        {/* History line */}
        <path
          d={pathD(histPoints)}
          fill="none"
          stroke="#38bdf8"
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#glowLine)"
          className="transition-all duration-1000"
          style={{ clipPath: animated ? 'inset(0 0 0 0)' : 'inset(0 100% 0 0)' }}
        />

        {/* Forecast line */}
        <path d={pathD(forePoints)} fill="none" stroke="#38bdf880" strokeWidth={1.5} strokeDasharray="6,3" strokeLinecap="round" strokeLinejoin="round" />

        {/* Divider */}
        <line x1={dividerX} y1={pad.top} x2={dividerX} y2={pad.top + innerH} stroke="#374151" strokeWidth={1} strokeDasharray="4,4" />

        {/* Data points */}
        {histPoints.map((p, i) => (
          <g key={`h-${i}`} className="transition-all duration-500" style={{ transitionDelay: `${i * 0.05}s`, opacity: animated ? 1 : 0 }}>
            <circle cx={p.x} cy={p.y} r={4} fill="#0c4a6e" stroke="#38bdf8" strokeWidth={2} />
            <circle cx={p.x} cy={p.y} r={8} fill="rgba(56,189,248,0.1)" className="animate-pulse-ring" />
          </g>
        ))}
        {forePoints.map((p, i) => (
          <circle key={`f-${i}`} cx={p.x} cy={p.y} r={3} fill="#075985" stroke="#38bdf880" strokeWidth={1.5} opacity={animated ? 1 : 0} className="transition-opacity duration-500" style={{ transitionDelay: `${(histPoints.length + i) * 0.05}s` }} />
        ))}

        {/* X-axis labels */}
        {data.map((d, i) => (
          <text key={`xl-${i}`} x={pad.left + (i / (data.length - 1)) * innerW} y={pad.top + innerH + 16} textAnchor="middle" fill="#4b5563" fontSize="7" fontFamily="JetBrains Mono, monospace">{d.hour}</text>
        ))}
        {forecast.map((d, i) => (
          <text key={`fl-${i}`} x={pad.left + ((data.length - 1 + i) / (data.length + forecast.length - 1)) * innerW} y={pad.top + innerH + 16} textAnchor="middle" fill="#4b5563" fontSize="7" fontFamily="JetBrains Mono, monospace">{d.hour}</text>
        ))}
      </svg>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-800/40">
        <span className="text-[9px] text-gray-500">GraphCast + TFT Ensemble</span>
        <span className="text-[9px] flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-gray-500">Live</span>
        </span>
      </div>
    </div>
  )
}
