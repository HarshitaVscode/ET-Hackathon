'use client';

import React, { useState, useEffect, createContext, useContext } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

type Theme = 'dark' | 'light';
interface ThemeCtx { theme: Theme; toggle: () => void }
const ThemeCtx_ = createContext<ThemeCtx>({ theme: 'dark', toggle: () => {} });
export const useTheme = () => useContext(ThemeCtx_);

const navItems = [
  { label: 'Overview', href: '/forecast-dashboard', icon: '◉' },
  { label: 'Historical', href: '/forecast-dashboard/historical', icon: '◈' },
  { label: 'Forecast', href: '/forecast-dashboard/forecast', icon: '◎' },
  { label: 'Map', href: '/forecast-dashboard/map', icon: '◐' },
  { label: 'Calculator', href: '/forecast-dashboard/calculator', icon: '◇' },
  { label: 'Weather', href: '/forecast-dashboard/weather', icon: '○' },
  { label: 'Analytics', href: '/forecast-dashboard/analytics', icon: '◈' },
];

const aqiColors: Record<string, string> = {
  Good: '#22c55e', Satisfactory: '#84cc16', Moderate: '#eab308',
  Poor: '#f97316', 'Very Poor': '#ef4444', Severe: '#be123c',
};

export function getAQIColor(v: number): string {
  if (v <= 50) return aqiColors.Good;
  if (v <= 100) return aqiColors.Satisfactory;
  if (v <= 200) return aqiColors.Moderate;
  if (v <= 300) return aqiColors.Poor;
  if (v <= 400) return aqiColors['Very Poor'];
  return aqiColors.Severe;
}

export function getAQICategory(v: number): string {
  if (v <= 50) return 'Good';
  if (v <= 100) return 'Satisfactory';
  if (v <= 200) return 'Moderate';
  if (v <= 300) return 'Poor';
  if (v <= 400) return 'Very Poor';
  return 'Severe';
}

export default function ForecastDashboardLayout({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  useEffect(() => { setMounted(true); }, []);

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  if (!mounted) return <div className="h-screen bg-[#0a0a1a]" />;

  return (
    <ThemeCtx_.Provider value={{ theme, toggle }}>
      <div className={`${theme === 'dark' ? 'bg-[#0a0a1a] text-gray-100' : 'bg-gray-50 text-gray-900'} min-h-screen transition-colors duration-500`}>
        <style>{`
          @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
          @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
          @keyframes pulseGlow { 0%, 100% { box-shadow: 0 0 20px rgba(59,130,246,0.15); } 50% { box-shadow: 0 0 40px rgba(59,130,246,0.3); } }
          @keyframes aqiPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
          @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
          .glass { background: ${theme === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.7)'}; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}; }
          .glass-strong { background: ${theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.85)'}; backdrop-filter: blur(30px); -webkit-backdrop-filter: blur(30px); border: 1px solid ${theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}; }
          .animate-fadeIn { animation: fadeIn 0.6s ease-out both; }
          .animate-slideIn { animation: slideIn 0.5s ease-out both; }
          .animate-pulseGlow { animation: pulseGlow 3s ease-in-out infinite; }
          .shimmer { background: linear-gradient(90deg, transparent, ${theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)'}, transparent); background-size: 200% 100%; animation: shimmer 2s infinite; }
          .aqi-gradient-good { background: linear-gradient(135deg, #22c55e, #16a34a); }
          .aqi-gradient-satisfactory { background: linear-gradient(135deg, #84cc16, #65a30d); }
          .aqi-gradient-moderate { background: linear-gradient(135deg, #eab308, #ca8a04); }
          .aqi-gradient-poor { background: linear-gradient(135deg, #f97316, #ea580c); }
          .aqi-gradient-very-poor { background: linear-gradient(135deg, #ef4444, #dc2626); }
          .aqi-gradient-severe { background: linear-gradient(135deg, #be123c, #9f1239); }
          .scrollbar-thin::-webkit-scrollbar { width: 4px; }
          .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
          .scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        `}</style>

        {/* Sidebar */}
        <aside className={`fixed top-0 left-0 h-full z-40 transition-all duration-300 ${sidebarOpen ? 'w-56' : 'w-16'} ${theme === 'dark' ? 'bg-[#0d0d2b]/90' : 'bg-white/90'} backdrop-blur-xl border-r ${theme === 'dark' ? 'border-white/5' : 'border-black/5'}`}>
          <div className="flex items-center gap-2 h-16 px-4 border-b border-white/5">
            <div className="w-8 h-8 rounded-lg aqi-gradient-poor flex items-center justify-center text-white text-xs font-bold">F</div>
            {sidebarOpen && <span className="text-sm font-semibold tracking-wide">ForecastIQ</span>}
          </div>
          <nav className="py-4 px-2 space-y-1">
            {navItems.map(item => {
              const active = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                    active
                      ? theme === 'dark' ? 'bg-blue-500/15 text-blue-400' : 'bg-blue-50 text-blue-600'
                      : theme === 'dark' ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-500 hover:text-gray-800 hover:bg-black/5'
                  }`}>
                  <span className="text-lg">{item.icon}</span>
                  {sidebarOpen && <span>{item.label}</span>}
                  {active && sidebarOpen && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500" />}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Top Bar */}
        <header className={`fixed top-0 right-0 z-30 h-16 flex items-center justify-between px-6 transition-all duration-300 ${sidebarOpen ? 'left-56' : 'left-16'} ${theme === 'dark' ? 'bg-[#0a0a1a]/80' : 'bg-gray-50/80'} backdrop-blur-xl border-b ${theme === 'dark' ? 'border-white/5' : 'border-black/5'}`}>
          <div className="flex items-center gap-4">
            <button onClick={() => setSidebarOpen(o => !o)} className={`p-2 rounded-lg ${theme === 'dark' ? 'hover:bg-white/5' : 'hover:bg-black/5'} transition-colors`}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M2.5 5h15M2.5 10h15M2.5 15h15"/></svg>
            </button>
            <div className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
              <span className="text-blue-400 font-medium">ForecastIQ</span> / {navItems.find(i => i.href === pathname)?.label || 'Overview'}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
              <span>Updated: <span className="text-gray-300">just now</span></span>
            </div>
            <button onClick={toggle} className={`p-2 rounded-lg ${theme === 'dark' ? 'hover:bg-white/5' : 'hover:bg-black/5'} transition-colors`}>
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className={`pt-16 transition-all duration-300 ${sidebarOpen ? 'ml-56' : 'ml-16'}`}>
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </ThemeCtx_.Provider>
  );
}
