'use client'

import { useState } from 'react'
import {
  LayoutDashboard, BarChart3, Shield, Users, MessageSquare, AlertTriangle, Settings,
  ChevronLeft, Bell, LogOut, Search,
} from 'lucide-react'

export type PageView = 'dashboard' | 'analytics' | 'enforcement' | 'citizens' | 'ai-chat' | 'emergency' | 'settings'

interface NavItem {
  id: PageView
  icon: typeof LayoutDashboard
  label: string
  badge?: string | number
  badgeColor?: string
}

const navItems: NavItem[] = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'analytics', icon: BarChart3, label: 'Analytics', badge: '3', badgeColor: 'badge-info' },
  { id: 'enforcement', icon: Shield, label: 'Enforcement', badge: '2', badgeColor: 'badge-warning' },
  { id: 'citizens', icon: Users, label: 'Citizens' },
  { id: 'ai-chat', icon: MessageSquare, label: 'AI Chat' },
  { id: 'emergency', icon: AlertTriangle, label: 'Emergency', badge: '1', badgeColor: 'badge-critical' },
  { id: 'settings', icon: Settings, label: 'Settings' },
]

interface DashboardLayoutProps {
  children: React.ReactNode
  activePage: PageView
  onNavigate: (page: PageView) => void
}

export function DashboardLayout({ children, activePage, onNavigate }: DashboardLayoutProps) {
  const [sidebarHovered, setSidebarHovered] = useState(false)

  const expanded = sidebarHovered

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`relative flex flex-col bg-gray-900/90 border-r border-gray-800/60 transition-all duration-300 ease-in-out z-20 ${
          expanded ? 'w-56' : 'w-16'
        }`}
        onMouseEnter={() => setSidebarHovered(true)}
        onMouseLeave={() => setSidebarHovered(false)}
      >
        {/* Logo */}
        <div className={`flex items-center h-14 border-b border-gray-800/60 px-3 ${expanded ? 'justify-between' : 'justify-center'}`}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-vayu-400 via-vayu-500 to-vayu-700 flex items-center justify-center shadow-lg shadow-vayu-500/20 flex-shrink-0">
              <span className="text-white font-bold text-sm">V</span>
            </div>
            {expanded && (
              <div>
                <span className="text-sm font-semibold text-white">Vayu-Drishti</span>
                <p className="text-[9px] text-gray-500 uppercase tracking-widest">Air Quality System</p>
              </div>
            )}
          </div>
          {expanded && (
            <button className="text-gray-500 hover:text-gray-300 transition-colors">
              <ChevronLeft size={16} />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-1 overflow-hidden">
          {navItems.map((item) => {
            const isActive = activePage === item.id
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 rounded-lg transition-all duration-200 ${
                  expanded ? 'px-3 py-2.5' : 'px-2 py-2.5 justify-center'
                } ${
                  isActive
                    ? 'bg-vayu-600/15 text-vayu-400 border border-vayu-600/20 shadow-sm shadow-vayu-600/5'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                }`}
                title={!expanded ? item.label : undefined}
              >
                <Icon size={expanded ? 18 : 20} className="flex-shrink-0" />
                {expanded && (
                  <>
                    <span className="flex-1 text-left text-sm">{item.label}</span>
                    {item.badge && (
                      <span className={`badge ${item.badgeColor} text-[9px] px-1.5 py-0`}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            )
          })}
        </nav>

        {/* Bottom section */}
        <div className={`p-2 border-t border-gray-800/60 ${expanded ? 'px-3' : ''}`}>
          <button
            className={`w-full flex items-center gap-3 rounded-lg transition-all duration-200 text-gray-400 hover:text-red-400 hover:bg-red-500/5 ${
              expanded ? 'px-3 py-2.5' : 'px-2 py-2.5 justify-center'
            }`}
          >
            <LogOut size={expanded ? 18 : 20} />
            {expanded && <span className="text-sm">Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b border-gray-800/60 flex items-center justify-between px-5 bg-gray-950/70 backdrop-blur-xl z-10">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Search anything..."
                className="w-64 bg-gray-900/80 border border-gray-800/60 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-300 placeholder-gray-500 focus:outline-none focus:border-vayu-500/40 focus:ring-1 focus:ring-vayu-500/10 transition-all"
              />
            </div>
            <div className="flex items-center gap-2 text-[11px] text-gray-500 bg-gray-900/50 px-2.5 py-1 rounded-full border border-gray-800/40">
              <span className="text-gray-400">Delhi, India</span>
              <span className="text-gray-600">•</span>
              <span>18 Jul 2026</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick status */}
            <div className="flex items-center gap-3 px-3 py-1 rounded-lg bg-gray-900/60 border border-gray-800/40">
              <div className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
                <span className="text-xs font-semibold text-red-400">285</span>
                <span className="text-[10px] text-gray-500">AQI</span>
              </div>
              <div className="w-px h-4 bg-gray-800" />
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-gray-400">PM2.5</span>
                <span className="text-xs font-medium text-gray-200">128</span>
              </div>
            </div>

            {/* Notifications */}
            <button className="relative p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 transition-all">
              <Bell size={16} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 border border-gray-950" />
            </button>

            {/* Avatar */}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vayu-500 to-vayu-700 flex items-center justify-center shadow-md shadow-vayu-500/20">
              <span className="text-[10px] font-bold text-white">JD</span>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6 bg-gray-950/30">
          {children}
        </main>
      </div>
    </div>
  )
}
