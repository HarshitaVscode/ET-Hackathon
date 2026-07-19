'use client'

import { EnforcementQueue } from '@/components/admin/EnforcementQueue'
import { AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react'

export function EnforcementView() {
  const stats = [
    { label: 'Active Cases', value: '12', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'Resolved Today', value: '5', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Avg Response', value: '24m', icon: Clock, color: 'text-vayu-400', bg: 'bg-vayu-500/10' },
    { label: 'Resolution Rate', value: '87%', icon: TrendingUp, color: 'text-purple-400', bg: 'bg-purple-500/10' },
  ]

  return (
    <div className="space-y-6">
      <div className="mb-2">
        <h2 className="text-lg font-semibold">Enforcement</h2>
        <p className="text-xs text-gray-500 mt-1">Monitor and manage compliance actions across Delhi</p>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {stats.map((s) => {
          const Icon = s.icon
          return (
            <div key={s.label} className="card flex items-center gap-4">
              <div className={`w-10 h-10 rounded-xl ${s.bg} flex items-center justify-center`}>
                <Icon size={18} className={s.color} />
              </div>
              <div>
                <p className="text-lg font-bold">{s.value}</p>
                <p className="text-[10px] text-gray-500">{s.label}</p>
              </div>
            </div>
          )
        })}
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-7">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Enforcement Queue</h3>
              <div className="flex items-center gap-2">
                <button className="text-[10px] text-gray-500 hover:text-gray-300 px-2 py-1 rounded bg-gray-800/50">All</button>
                <button className="text-[10px] text-vayu-400 px-2 py-1 rounded bg-vayu-600/10">Priority</button>
              </div>
            </div>
            <EnforcementQueue compact={false} />
          </div>
        </div>
        <div className="col-span-12 lg:col-span-5 space-y-5">
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Squad Deployment</h3>
            <div className="space-y-3">
              {[
                { squad: 'SQ-01', status: 'active', location: 'Ghaziabad', eta: '12 min', members: 3 },
                { squad: 'SQ-02', status: 'active', location: 'Dwarka', eta: '8 min', members: 2 },
                { squad: 'SQ-03', status: 'standby', location: 'HQ', eta: '—', members: 4 },
              ].map((s) => (
                <div key={s.squad} className="flex items-center justify-between p-2.5 rounded-lg bg-gray-800/40 border border-gray-800/40">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                      s.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700/50 text-gray-400'
                    }`}>
                      {s.squad}
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-200">{s.location}</p>
                      <p className="text-[10px] text-gray-500">{s.members} members • ETA {s.eta}</p>
                    </div>
                  </div>
                  <span className={`badge text-[9px] ${s.status === 'active' ? 'badge-success' : 'badge-info'}`}>
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Recent Actions</h3>
            <div className="space-y-2">
              {[
                { action: 'Construction site sealed', ward: 'Dwarka Sector 15', time: '15 min ago', type: 'warning' },
                { action: 'Fine issued — open burning', ward: 'Ghaziabad', time: '42 min ago', type: 'critical' },
                { action: 'Anti-smog guns deployed', ward: 'Civil Lines', time: '1h ago', type: 'info' },
              ].map((a, i) => (
                <div key={i} className="flex items-start gap-2 py-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${
                    a.type === 'critical' ? 'bg-red-500' : a.type === 'warning' ? 'bg-amber-500' : 'bg-vayu-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-xs text-gray-300">{a.action}</p>
                    <p className="text-[10px] text-gray-500">{a.ward} • {a.time}</p>
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
