'use client'

import { useState } from 'react'
import { DashboardLayout, type PageView } from '@/components/DashboardLayout'
import { CityMap } from '@/components/map/CityMap'
import { AQIStatsBar } from '@/components/AQIStatsBar'
import { SourceDonut } from '@/components/charts/SourceDonut'
import { AQITrendChart } from '@/components/charts/AQITrendChart'
import { AlertPanel } from '@/components/AlertPanel'
import { EnforcementQueue } from '@/components/admin/EnforcementQueue'
import { AIAssistant } from '@/components/ai-chat/AIAssistant'
import { AnalyticsView } from '@/components/views/AnalyticsView'
import { EnforcementView } from '@/components/views/EnforcementView'
import { CitizensView } from '@/components/views/CitizensView'
import { EmergencyView } from '@/components/views/EmergencyView'

export default function DashboardPage() {
  const [activePage, setActivePage] = useState<PageView>('dashboard')
  const [showChat, setShowChat] = useState(false)

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardView showChat={showChat} setShowChat={setShowChat} />
      case 'analytics':
        return <AnalyticsView />
      case 'enforcement':
        return <EnforcementView />
      case 'citizens':
        return <CitizensView />
      case 'ai-chat':
        return <AIChatView />
      case 'emergency':
        return <EmergencyView />
      case 'settings':
        return <SettingsView />
      default:
        return <DashboardView showChat={showChat} setShowChat={setShowChat} />
    }
  }

  return (
    <DashboardLayout activePage={activePage} onNavigate={setActivePage}>
      <div className="animate-fade-in h-full" key={activePage}>
        {renderPage()}
      </div>
    </DashboardLayout>
  )
}

function DashboardView({ showChat, setShowChat }: { showChat: boolean; setShowChat: (v: boolean) => void }) {
  return (
    <div className="grid grid-cols-12 gap-4 lg:gap-5 h-full">
      {/* Left sidebar */}
      <div className="col-span-12 lg:col-span-3 space-y-4">
        <AQIStatsBar />
        <SourceDonut />
        <AlertPanel />
        <EnforcementQueue compact />
      </div>

      {/* Main map */}
      <div className="col-span-12 lg:col-span-6 relative">
        <div className="absolute top-3 left-3 z-10 flex gap-2">
          <button className="px-3 py-1.5 rounded-lg text-xs font-medium bg-vayu-600/20 text-vayu-400 border border-vayu-600/30 backdrop-blur-sm shadow-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-vayu-400 animate-pulse" />
              2D Map
            </span>
          </button>
          <button className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-900/60 text-gray-400 border border-gray-800/40 backdrop-blur-sm hover:bg-gray-800/60 transition-colors">
            3D Twin
          </button>
        </div>
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-gray-900/70 backdrop-blur-sm rounded-lg px-2.5 py-1.5 border border-gray-800/50 text-[10px] text-gray-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Live
        </div>
        <CityMap />
      </div>

      {/* Right panel */}
      <div className="col-span-12 lg:col-span-3 space-y-4">
        <AQITrendChart />
        <div className="card glass-card-accent">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-vayu-400" />
              <h3 className="text-xs font-semibold text-gray-300">AI Assistant</h3>
            </div>
            <button
              onClick={() => setShowChat(!showChat)}
              className="text-[10px] text-vayu-400 hover:text-vayu-300 font-medium transition-colors"
            >
              {showChat ? 'Collapse' : 'Expand'}
            </button>
          </div>
          <div className={showChat ? 'h-[400px]' : ''}>
            <AIAssistant compact={!showChat} />
          </div>
        </div>
      </div>
    </div>
  )
}

function AIChatView() {
  return (
    <div className="max-w-3xl mx-auto h-[calc(100vh-7rem)]">
      <div className="card h-full flex flex-col">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-800/60 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-vayu-400 to-vayu-600 flex items-center justify-center">
            <MessageSquare size={18} className="text-white" />
          </div>
          <div>
            <h2 className="text-sm font-semibold">AirGPT Assistant</h2>
            <p className="text-[10px] text-gray-500">Powered by Llama 3 + rule-based fallback</p>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <AIAssistant compact={false} />
        </div>
      </div>
    </div>
  )
}

import { MessageSquare } from 'lucide-react'

function SettingsView() {
  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Settings</h2>
        <p className="text-xs text-gray-500 mt-1">Configure system preferences and integrations</p>
      </div>
      <div className="card space-y-4">
        <div className="flex items-center justify-between py-2">
          <div>
            <p className="text-sm font-medium text-gray-200">Data Refresh Interval</p>
            <p className="text-[10px] text-gray-500">How often to poll sensor data</p>
          </div>
          <select className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300">
            <option>5 minutes</option>
            <option>15 minutes</option>
            <option>30 minutes</option>
            <option>1 hour</option>
          </select>
        </div>
        <div className="border-t border-gray-800/60" />
        <div className="flex items-center justify-between py-2">
          <div>
            <p className="text-sm font-medium text-gray-200">Alert Threshold</p>
            <p className="text-[10px] text-gray-500">AQI level for critical alerts</p>
          </div>
          <select className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300">
            <option>AQI &gt; 200</option>
            <option>AQI &gt; 300</option>
            <option>AQI &gt; 400</option>
          </select>
        </div>
        <div className="border-t border-gray-800/60" />
        <div className="flex items-center justify-between py-2">
          <div>
            <p className="text-sm font-medium text-gray-200">Notifications</p>
            <p className="text-[10px] text-gray-500">Email and Slack alerts</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" className="sr-only peer" defaultChecked />
            <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-vayu-600" />
          </label>
        </div>
      </div>
    </div>
  )
}
