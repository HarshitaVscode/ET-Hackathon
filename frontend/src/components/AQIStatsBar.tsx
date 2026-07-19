'use client'

import { TrendingUp, TrendingDown, Minus, Gauge, Wind, CloudRain, Thermometer } from 'lucide-react'

const stats = [
  { label: 'AQI', value: '285', unit: 'Poor', color: 'from-red-500 to-red-600', textColor: 'text-red-400', bgColor: 'bg-red-500/10', icon: Gauge, trend: 'up' as const, change: '+12' },
  { label: 'PM2.5', value: '128', unit: 'μg/m³', color: 'from-orange-500 to-red-500', textColor: 'text-orange-400', bgColor: 'bg-orange-500/10', icon: Wind, trend: 'up' as const, change: '+8' },
  { label: 'PM10', value: '245', unit: 'μg/m³', color: 'from-purple-500 to-pink-500', textColor: 'text-purple-400', bgColor: 'bg-purple-500/10', icon: CloudRain, trend: 'down' as const, change: '-5' },
  { label: 'Temp', value: '34°', unit: 'C', color: 'from-amber-400 to-orange-500', textColor: 'text-amber-400', bgColor: 'bg-amber-500/10', icon: Thermometer, trend: 'up' as const, change: '+1' },
]

const TrendIcon = ({ trend }: { trend: string }) => {
  if (trend === 'up') return <TrendingUp size={10} className="text-red-400" />
  if (trend === 'down') return <TrendingDown size={10} className="text-emerald-400" />
  return <Minus size={10} className="text-gray-400" />
}

export function AQIStatsBar() {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1 h-4 rounded-full bg-gradient-to-b from-vayu-400 to-vayu-600" />
        <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Current Conditions</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.label}
              className="relative p-3 rounded-xl bg-gray-800/40 border border-gray-800/40 hover:border-gray-700/60 transition-all duration-300 group animate-count-up"
              style={{ animationDelay: `${i * 0.08}s` }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className={`w-7 h-7 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <Icon size={13} className={stat.textColor} />
                </div>
                <div className="flex items-center gap-0.5">
                  <TrendIcon trend={stat.trend} />
                  <span className={`text-[9px] font-medium ${
                    stat.trend === 'up' ? 'text-red-400' : stat.trend === 'down' ? 'text-emerald-400' : 'text-gray-400'
                  }`}>{stat.change}</span>
                </div>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold tracking-tight text-white">{stat.value}</span>
                <span className="text-[9px] text-gray-500">{stat.unit}</span>
              </div>
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-gray-700/30 to-transparent" />
            </div>
          )
        })}
      </div>
    </div>
  )
}
