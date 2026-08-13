'use client';

import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  isPositive?: boolean;
  icon: LucideIcon;
  iconColor?: string;
  subtitle?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  isPositive = true,
  icon: Icon,
  iconColor = 'text-indigo-500',
  subtitle,
  className
}) => {
  return (
    <div className={cn("glass-panel-interactive p-5 rounded-2xl flex flex-col justify-between relative overflow-hidden group", className)}>
      {/* Background Accent Glow */}
      <div className="absolute -right-6 -top-6 w-20 h-20 rounded-full bg-indigo-500/5 group-hover:bg-indigo-500/10 blur-xl transition-all"></div>

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{title}</p>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1.5 tracking-tight">{value}</h3>
        </div>

        <div className={cn("p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200/50 dark:border-slate-700/50 shadow-sm", iconColor)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs">
        {change && (
          <div className={cn("flex items-center gap-1 font-semibold", isPositive ? "text-emerald-500" : "text-rose-500")}>
            {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            <span>{change}</span>
          </div>
        )}
        {subtitle && <span className="text-slate-400 dark:text-slate-500 text-[11px] font-medium">{subtitle}</span>}
      </div>
    </div>
  );
};
