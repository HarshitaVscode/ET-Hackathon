'use client'

import { AlertTriangle, Flame, Truck, Factory, ChevronRight } from 'lucide-react'

const alerts = [
  { type: 'critical', icon: Flame, message: 'Burning detected — Ghaziabad border', time: '5 min ago', action: 'Dispatch squad', reading: 'AQI 412' },
  { type: 'warning', icon: Truck, message: 'NH-9 congestion exceeds threshold', time: '12 min ago', action: 'Adjust signals', reading: 'CONG 8.5' },
  { type: 'warning', icon: Factory, message: 'Wazirpur industry emissions rising', time: '28 min ago', action: 'Schedule inspection', reading: 'PM2.5 180' },
  { type: 'info', icon: AlertTriangle, message: 'GRAP Stage 3 activated for East Delhi', time: '1h ago', action: 'View plan', reading: '' },
]

export function AlertPanel() {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1 h-4 rounded-full bg-gradient-to-b from-red-400 to-amber-500" />
        <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Active Alerts</h3>
        <span className="ml-auto text-[9px] text-red-400 font-semibold bg-red-500/10 px-1.5 py-0.5 rounded-full">{alerts.filter(a => a.type === 'critical').length} critical</span>
      </div>
      <div className="space-y-2">
        {alerts.map((alert, i) => {
          const Icon = alert.icon
          const isCritical = alert.type === 'critical'
          const isWarning = alert.type === 'warning'
          return (
            <div
              key={i}
              className={`group relative p-2.5 rounded-xl border transition-all duration-200 cursor-pointer hover:scale-[1.01] ${
                isCritical
                  ? 'bg-red-950/40 border-red-800/40 hover:bg-red-950/60 hover:border-red-700/50'
                  : isWarning
                    ? 'bg-amber-950/30 border-amber-800/30 hover:bg-amber-950/40 hover:border-amber-700/40'
                    : 'bg-vayu-950/20 border-vayu-800/20 hover:bg-vayu-950/30 hover:border-vayu-700/30'
              }`}
            >
              {/* Glow effect for critical */}
              {isCritical && (
                <div className="absolute -inset-px rounded-xl bg-gradient-to-br from-red-500/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              )}
              <div className="relative flex items-start gap-2.5">
                <div className={`p-1.5 rounded-lg flex-shrink-0 ${
                  isCritical ? 'bg-red-500/20' : isWarning ? 'bg-amber-500/20' : 'bg-vayu-500/20'
                }`}>
                  <Icon size={12} className={
                    isCritical ? 'text-red-400' : isWarning ? 'text-amber-400' : 'text-vayu-400'
                  } />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-xs font-medium truncate ${
                      isCritical ? 'text-red-200' : 'text-gray-200'
                    }`}>{alert.message}</p>
                    {alert.reading && (
                      <span className={`text-[9px] font-mono font-semibold flex-shrink-0 ${
                        isCritical ? 'text-red-400' : 'text-amber-400'
                      }`}>{alert.reading}</span>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-1.5">
                    <span className="text-[9px] text-gray-500">{alert.time}</span>
                    <button className="flex items-center gap-0.5 text-[9px] text-vayu-400 hover:text-vayu-300 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      {alert.action} <ChevronRight size={10} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
