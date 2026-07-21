'use client';

import React, { useState } from 'react';

interface Tab { id: string; label: string; }

interface TabsProps {
  tabs: Tab[];
  active?: string;
  onChange: (id: string) => void;
  className?: string;
}

export default function Tabs({ tabs, active, onChange, className = '' }: TabsProps) {
  return (
    <div className={`flex gap-1 p-1 rounded-xl ${className}`} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
      {tabs.map(tab => (
        <button key={tab.id} onClick={() => onChange(tab.id)}
          className={`relative px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
            (active || tabs[0]?.id) === tab.id
              ? 'text-white'
              : 'text-gray-500 hover:text-gray-300'
          }`}>
          {(active || tabs[0]?.id) === tab.id && (
            <span className="absolute inset-0 rounded-lg bg-blue-500/20 border border-blue-500/30" />
          )}
          <span className="relative z-10">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}

export function SegmentedControl({ options, value, onChange, className = '' }: {
  options: { label: string; value: string }[];
  value: string;
  onChange: (v: string) => void;
  className?: string;
}) {
  return (
    <div className={`flex gap-0.5 p-0.5 rounded-lg ${className}`} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
      {options.map(opt => (
        <button key={opt.value} onClick={() => onChange(opt.value)}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
            value === opt.value
              ? 'text-white shadow-sm'
              : 'text-gray-500 hover:text-gray-300'
          }`}
          style={value === opt.value ? { background: 'linear-gradient(135deg, rgba(59,130,246,0.3), rgba(99,102,241,0.3))', border: '1px solid rgba(59,130,246,0.3)' } : {}}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
