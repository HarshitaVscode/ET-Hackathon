'use client'

import { useEffect, useState } from 'react'

const sources = [
  { label: 'Traffic', percentage: 42, color: '#0ea5e9', gradient: 'from-sky-500 to-cyan-400' },
  { label: 'Burning', percentage: 28, color: '#f97316', gradient: 'from-orange-500 to-amber-400' },
  { label: 'Industry', percentage: 18, color: '#8b5cf6', gradient: 'from-violet-500 to-purple-400' },
  { label: 'Construction', percentage: 8, color: '#eab308', gradient: 'from-yellow-500 to-yellow-400' },
  { label: 'Other', percentage: 4, color: '#6b7280', gradient: 'from-gray-500 to-gray-400' },
]

export function SourceDonut() {
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [])

  const cx = 90, cy = 90, r = 72, ir = 48
  let currentAngle = -Math.PI / 2

  const getArc = (pct: number) => {
    const angle = (pct / 100) * Math.PI * 2
    const start = currentAngle
    const end = currentAngle + angle
    const sx = cx + r * Math.cos(start)
    const sy = cy + r * Math.sin(start)
    const ex = cx + r * Math.cos(end)
    const ey = cy + r * Math.sin(end)
    const large = angle > Math.PI ? 1 : 0
    const isx = cx + ir * Math.cos(end)
    const isy = cy + ir * Math.sin(end)
    const iex = cx + ir * Math.cos(start)
    const iey = cy + ir * Math.sin(start)
    currentAngle = end
    return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey} L ${isx} ${isy} A ${ir} ${ir} 0 ${large} 0 ${iex} ${iey} Z`
  }

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1 h-4 rounded-full bg-gradient-to-b from-orange-400 to-amber-500" />
        <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Source Attribution</h3>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative flex-shrink-0">
          <svg width="180" height="180" viewBox="0 0 180 180" className="drop-shadow-lg">
            {/* Glow */}
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>
            {sources.map((s) => (
              <path
                key={s.label}
                d={getArc(s.percentage)}
                fill={s.color}
                opacity={animated ? 0.9 : 0}
                className="transition-all duration-700 ease-out"
                style={{ transitionDelay: `${sources.indexOf(s) * 0.1}s` }}
                filter="url(#glow)"
              />
            ))}
            {/* Inner circle */}
            <circle cx={cx} cy={cy} r={ir - 4} fill="#111827" stroke="#1f2937" strokeWidth="1" />
            {/* Center value */}
            <text x={cx} y={cy - 6} textAnchor="middle" fill="white" fontSize="22" fontWeight="800" fontFamily="Inter, sans-serif">
              285
            </text>
            <text x={cx} y={cy + 12} textAnchor="middle" fill="#9ca3af" fontSize="9" fontWeight="500" letterSpacing="2" fontFamily="Inter, sans-serif">
              AQI
            </text>
            {/* Decorative dots */}
            <circle cx={cx - 25} cy={cy + 20} r="1.5" fill="#374151" />
            <circle cx={cx + 25} cy={cy + 20} r="1.5" fill="#374151" />
          </svg>
        </div>
        <div className="flex-1 space-y-1.5">
          {sources.map((s) => (
            <div key={s.label} className="group cursor-pointer">
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                  <span className="text-xs text-gray-300 group-hover:text-white transition-colors">{s.label}</span>
                </div>
                <span className="text-xs font-semibold text-gray-200">{s.percentage}%</span>
              </div>
              <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-1000 ease-out"
                  style={{
                    width: animated ? `${s.percentage}%` : '0%',
                    backgroundColor: s.color,
                    opacity: 0.7,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800/40">
        <span className="text-[9px] text-gray-500">CausalNex DAG • 85% confidence</span>
        <span className="text-[9px] text-vayu-400 font-medium">Updated 5 min ago</span>
      </div>
    </div>
  )
}
