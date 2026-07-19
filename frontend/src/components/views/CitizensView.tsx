'use client'

import { MessageSquare, User, MapPin, Clock } from 'lucide-react'

export function CitizensView() {
  const reports = [
    { id: 'CR-A3F8', citizen: 'CIT-A1', type: 'Burning', location: 'Sector 12 Market', time: '12 min ago', status: 'pending', severity: 4 },
    { id: 'CR-B7C2', citizen: 'CIT-B4', type: 'Construction', location: 'Plot 47, Dwarka', time: '35 min ago', status: 'verified', severity: 3 },
    { id: 'CR-D4E9', citizen: 'CIT-C7', type: 'Haze', location: 'Ring Road Junction', time: '1h ago', status: 'verified', severity: 2 },
    { id: 'CR-F1A5', citizen: 'CIT-D2', type: 'Smell', location: 'Wazirpur Industrial', time: '2h ago', status: 'rejected', severity: 3 },
  ]

  return (
    <div className="space-y-6">
      <div className="mb-2">
        <h2 className="text-lg font-semibold">Citizen Reports</h2>
        <p className="text-xs text-gray-500 mt-1">Community-sourced pollution reports from across Delhi</p>
      </div>
      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-8">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Recent Reports</h3>
              <div className="flex gap-1">
                <button className="px-2 py-1 text-[10px] rounded-md bg-vayu-600/20 text-vayu-400">All</button>
                <button className="px-2 py-1 text-[10px] rounded-md text-gray-500 hover:text-gray-300">Pending</button>
                <button className="px-2 py-1 text-[10px] rounded-md text-gray-500 hover:text-gray-300">Verified</button>
              </div>
            </div>
            <div className="space-y-1">
              {reports.map((r) => (
                <div key={r.id} className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-800/40 transition-colors cursor-pointer border border-transparent hover:border-gray-800/50">
                  <div className="w-9 h-9 rounded-lg bg-gray-800/60 flex items-center justify-center flex-shrink-0">
                    <MessageSquare size={15} className="text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-200">{r.id}</span>
                      <span className={`badge text-[9px] ${
                        r.status === 'verified' ? 'badge-success' : r.status === 'rejected' ? 'badge-critical' : 'badge-warning'
                      }`}>{r.status}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-[10px] text-gray-500">{r.type}</span>
                      <span className="text-[10px] text-gray-500">•</span>
                      <span className="text-[10px] text-gray-500">{r.location}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-500">{r.time}</span>
                    <div className={`w-6 h-6 rounded flex items-center justify-center text-[9px] font-bold ${
                      r.severity >= 4 ? 'bg-red-500/20 text-red-400' : r.severity >= 3 ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-700/50 text-gray-400'
                    }`}>{r.severity}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-4 space-y-5">
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Report Stats</h3>
            <div className="space-y-4">
              {[
                { label: 'Total Reports', value: '47', color: 'text-vayu-400' },
                { label: 'Verified', value: '31', color: 'text-emerald-400' },
                { label: 'Pending Review', value: '12', color: 'text-amber-400' },
                { label: 'Rejected', value: '4', color: 'text-red-400' },
              ].map((s) => (
                <div key={s.label} className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{s.label}</span>
                  <span className={`text-sm font-bold ${s.color}`}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-3">Top Reporters</h3>
            <div className="space-y-2">
              {[
                { name: 'Rahul K.', reports: 8, avatar: 'RK' },
                { name: 'Priya S.', reports: 5, avatar: 'PS' },
                { name: 'Amit V.', reports: 3, avatar: 'AV' },
              ].map((r) => (
                <div key={r.name} className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-vayu-500 to-purple-500 flex items-center justify-center text-[9px] font-bold">
                    {r.avatar}
                  </div>
                  <span className="text-xs text-gray-300 flex-1">{r.name}</span>
                  <span className="text-[10px] text-gray-500">{r.reports} reports</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
