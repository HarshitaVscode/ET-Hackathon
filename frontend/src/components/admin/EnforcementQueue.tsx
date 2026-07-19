'use client'

import { ArrowRight, Clock, MapPin } from 'lucide-react'

interface EnforcementQueueProps {
  compact?: boolean
}

const items = [
  { id: 1, type: '🔥 Burning', location: 'Ghaziabad border', priority: 'HIGH', score: 0.92, ward: 'East Delhi', status: 'overdue' },
  { id: 2, type: '🏗️ Construction', location: 'Sector 15, Plot 47', priority: 'MEDIUM', score: 0.78, ward: 'Dwarka', status: 'pending' },
  { id: 3, type: '🏭 Industry', location: 'Wazirpur', priority: 'MEDIUM', score: 0.65, ward: 'Civil Lines', status: 'pending' },
  { id: 4, type: '🔥 Burning', location: 'Najafgarh drain', priority: 'LOW', score: 0.55, ward: 'Najafgarh', status: 'scheduled' },
]

const statusColors: Record<string, string> = {
  overdue: 'text-red-400 bg-red-500/10',
  pending: 'text-amber-400 bg-amber-500/10',
  scheduled: 'text-vayu-400 bg-vayu-500/10',
}

export function EnforcementQueue({ compact }: EnforcementQueueProps) {
  const displayItems = compact ? items.slice(0, 3) : items

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="w-1 h-4 rounded-full bg-gradient-to-b from-vayu-400 to-purple-500" />
          <h3 className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest">Enforcement Queue</h3>
        </div>
        <span className="text-[9px] text-gray-500 bg-gray-800/60 px-1.5 py-0.5 rounded-full">{items.length} items</span>
      </div>
      <div className="space-y-1.5">
        {displayItems.map((item, i) => (
          <div
            key={item.id}
            className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-gray-800/40 transition-all duration-200 cursor-pointer border border-transparent hover:border-gray-800/50 animate-slide-up group"
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs flex-shrink-0 ${
              item.priority === 'HIGH' ? 'bg-red-500/15' : item.priority === 'MEDIUM' ? 'bg-amber-500/15' : 'bg-gray-700/40'
            }`}>
              <span className="text-sm">{item.type.split(' ')[0]}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-xs text-gray-200 truncate">{item.location}</p>
                <span className={`text-[8px] px-1 py-0.5 rounded-full font-medium ${statusColors[item.status]}`}>
                  {item.status}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-[9px] font-medium ${
                  item.priority === 'HIGH' ? 'text-red-400' : 'text-amber-400'
                }`}>
                  {item.priority}
                </span>
                <span className="text-[8px] text-gray-500">•</span>
                <span className="text-[8px] text-gray-500">{Math.round(item.score * 100)}% confidence</span>
              </div>
            </div>
            <button className="p-1.5 rounded-lg text-gray-500 hover:text-vayu-400 hover:bg-vayu-500/10 opacity-0 group-hover:opacity-100 transition-all">
              <ArrowRight size={12} />
            </button>
          </div>
        ))}
      </div>
      {!compact && (
        <div className="mt-3 pt-3 border-t border-gray-800/40 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[9px] text-gray-500">
            <Clock size={10} />
            <span>Avg response: 24 min</span>
          </div>
          <button className="text-[9px] text-vayu-400 hover:text-vayu-300 font-medium transition-colors">
            View all ({items.length} items) →
          </button>
        </div>
      )}
    </div>
  )
}
