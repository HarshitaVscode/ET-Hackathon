'use client'

import { AlertTriangle, Flame, Wind, Users, Phone, Truck } from 'lucide-react'

export function EmergencyView() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-lg font-semibold">Emergency Response</h2>
          <p className="text-xs text-gray-500 mt-1">Real-time crisis management and resource coordination</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
          </span>
          <span className="text-xs font-semibold text-red-400">ACTIVE EMERGENCY</span>
        </div>
      </div>

      {/* Critical banner */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-red-950/80 via-red-900/60 to-amber-950/80 border border-red-800/40 p-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,50,0,0.1),transparent_50%)]" />
        <div className="relative flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
            <AlertTriangle size={24} className="text-red-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-bold text-red-300">Critical AQI Alert — East Delhi</h3>
            <p className="text-xs text-red-400/80 mt-0.5">AQI 412 (Severe) • Population at risk: 12,000 • GRAP Stage 4 activated</p>
          </div>
          <button className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-lg shadow-red-600/20">
            View Response Plan
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7 space-y-5">
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Affected Wards', value: '4', icon: MapPin, color: 'text-red-400' },
              { label: 'Population at Risk', value: '45K', icon: Users, color: 'text-amber-400' },
              { label: 'Squads Deployed', value: '6', icon: Truck, color: 'text-vayu-400' },
              { label: 'Hotlines Active', value: '3', icon: Phone, color: 'text-emerald-400' },
            ].map((s) => {
              const Icon = s.icon
              return (
                <div key={s.label} className="card flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl bg-gray-800/60 flex items-center justify-center ${s.color}`}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <p className="text-lg font-bold">{s.value}</p>
                    <p className="text-[10px] text-gray-500">{s.label}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="card">
            <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3">GRAP Stage 4 — Active Measures</h3>
            <div className="space-y-2">
              {[
                { action: 'Truck entry stopped (essential only)', status: 'active', icon: Truck },
                { action: 'Schools and colleges closed', status: 'active', icon: Users },
                { action: 'Odd-even vehicle scheme implemented', status: 'active', icon: Wind },
                { action: '50% WFH for offices', status: 'pending', icon: Users },
                { action: 'Construction & demolition banned', status: 'active', icon: Wind },
              ].map((m, i) => {
                const Icon = m.icon
                return (
                  <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-gray-800/30 border border-gray-800/40">
                    <Icon size={14} className={m.status === 'active' ? 'text-vayu-400' : 'text-gray-500'} />
                    <span className="flex-1 text-xs text-gray-300">{m.action}</span>
                    <span className={`badge text-[9px] ${m.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                      {m.status}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 space-y-5">
          <div className="card gradient-border">
            <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3">Resources</h3>
            <div className="space-y-3">
              {[
                { resource: 'Water Tankers', total: 24, available: 18, unit: 'units' },
                { resource: 'Anti-smog Guns', total: 12, available: 7, unit: 'units' },
                { resource: 'Enforcement Squads', total: 8, available: 3, unit: 'teams' },
                { resource: 'Medical Teams', total: 6, available: 4, unit: 'teams' },
              ].map((r) => (
                <div key={r.resource}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400">{r.resource}</span>
                    <span className="text-[10px] text-gray-500">{r.available}/{r.total} {r.unit}</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${(r.available / r.total) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card glass-card-warning">
            <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3">Emergency Contacts</h3>
            <div className="space-y-2">
              {[
                { dept: 'Pollution Control', number: '1800-123-456', icon: Phone },
                { dept: 'Emergency Services', number: '112', icon: AlertTriangle },
                { dept: 'Health Advisory', number: '1075', icon: Users },
              ].map((c) => {
                const Icon = c.icon
                return (
                  <div key={c.dept} className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/40">
                    <Icon size={14} className="text-gray-400" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-300">{c.dept}</p>
                      <p className="text-[10px] font-mono text-vayu-400">{c.number}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function MapPin(props: any) { return <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> }
