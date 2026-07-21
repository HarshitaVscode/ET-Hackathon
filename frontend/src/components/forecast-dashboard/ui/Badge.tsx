'use client';

import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md';
  className?: string;
}

const variants: Record<string, { bg: string; text: string; border: string }> = {
  default: { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20' },
  success: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
  warning: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  danger: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  info: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
};

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }: BadgeProps) {
  const v = variants[variant];
  return (
    <span className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${v.bg} ${v.text} ${v.border} ${
      size === 'sm' ? 'px-2.5 py-0.5 text-[10px]' : 'px-3 py-1 text-xs'
    } ${className}`}>
      {children}
    </span>
  );
}
