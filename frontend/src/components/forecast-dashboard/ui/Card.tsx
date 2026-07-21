'use client';

import React, { useRef, useState } from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  expandable?: boolean;
  onRefresh?: () => void;
  fullWidth?: boolean;
}

export default function Card({ children, className = '', title, subtitle, action, expandable, onRefresh, fullWidth }: CardProps) {
  const [expanded, setExpanded] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [showFull, setShowFull] = useState(false);

  const handleShare = () => {
    const text = title ? `${title}: ${document.title}` : document.title;
    if (navigator.share) { navigator.share({ title, text }); }
    else { navigator.clipboard.writeText(window.location.href); }
    setMenuOpen(false);
  };

  const handleDownload = () => {
    const el = contentRef.current;
    if (!el) return;
    import('html2canvas').then(mod => {
      mod.default(el).then(canvas => {
        const a = document.createElement('a');
        a.download = `${title || 'chart'}.png`;
        a.href = canvas.toDataURL();
        a.click();
      });
    }).catch(() => {
      alert('Download not available');
    });
    setMenuOpen(false);
  };

  return (
    <div className={`relative group animate-fadeIn ${fullWidth ? 'col-span-full' : ''}`}>
      <div className={`rounded-2xl p-5 transition-all duration-300 ${className}`}
        style={{
          background: 'rgba(255,255,255,0.04)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}
        onMouseEnter={() => {}}
      >
        {/* Hover glow */}
        <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
          style={{ background: 'radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(59,130,246,0.06), transparent 40%)' }}
          onMouseMove={(e) => {
            const rect = (e.currentTarget.parentElement as HTMLElement).getBoundingClientRect();
            (e.currentTarget as HTMLElement).style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
            (e.currentTarget as HTMLElement).style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
          }}
        />

        {/* Header */}
        {(title || subtitle || action || onRefresh) && (
          <div className="flex items-center justify-between mb-4 relative">
            <div>
              {title && <h3 className="text-sm font-semibold text-gray-200">{title}</h3>}
              {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
            </div>
            <div className="flex items-center gap-2">
              {action}
              {onRefresh && (
                <button onClick={onRefresh} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors" title="Refresh">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
                </button>
              )}
              <div className="relative">
                <button onClick={() => setMenuOpen(o => !o)} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
                </button>
                {menuOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                    <div className="absolute right-0 top-8 z-50 w-36 py-1 rounded-xl backdrop-blur-xl border border-white/10 bg-[#1a1a3e]/95 shadow-xl">
                      {expandable && <button onClick={() => { setShowFull(o => !o); setMenuOpen(false); }} className="w-full text-left px-3 py-2 text-xs text-gray-300 hover:bg-white/5">{showFull ? 'Minimize' : 'Expand'}</button>}
                      <button onClick={handleDownload} className="w-full text-left px-3 py-2 text-xs text-gray-300 hover:bg-white/5">Download PNG</button>
                      <button onClick={handleShare} className="w-full text-left px-3 py-2 text-xs text-gray-300 hover:bg-white/5">Share</button>
                      {expandable && <button onClick={() => { setExpanded(o => !o); setMenuOpen(false); }} className="w-full text-left px-3 py-2 text-xs text-gray-300 hover:bg-white/5">{expanded ? 'Collapse' : 'Expand'}</button>}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={contentRef} className={`transition-all duration-300 ${showFull ? 'fixed inset-4 z-50 overflow-auto p-6 rounded-2xl bg-[#0a0a1a]/95 backdrop-blur-2xl border border-white/10' : ''}`}>
          {children}
        </div>
      </div>
    </div>
  );
}
