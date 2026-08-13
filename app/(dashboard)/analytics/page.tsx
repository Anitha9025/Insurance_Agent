'use client';

import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldAlert, 
  Zap, 
  CheckCircle2, 
  Clock, 
  Users,
  PieChart as PieIcon,
  Sparkles
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

const monthlyTrends = [
  { month: 'Jan', claims: 840, approved: 780, fraud: 12 },
  { month: 'Feb', claims: 910, approved: 850, fraud: 15 },
  { month: 'Mar', claims: 1050, approved: 980, fraud: 8 },
  { month: 'Apr', claims: 990, approved: 920, fraud: 11 },
  { month: 'May', claims: 1120, approved: 1040, fraud: 6 },
  { month: 'Jun', claims: 1240, approved: 1160, fraud: 9 },
  { month: 'Jul', claims: 1310, approved: 1220, fraud: 5 },
];

const slaData = [
  { range: '< 1 min', count: 420 },
  { range: '1-3 mins', count: 680 },
  { range: '3-5 mins', count: 210 },
  { range: '> 5 mins', count: 45 },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold uppercase tracking-wider">
              Executive Analytics Engine
            </span>
            <span className="text-xs text-slate-400">Live BI Metrics</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Claims & Multi-Agent AI Analytics
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Track approval rates, fraud reduction index, processing turnaround time (SLA), and AI recommendation acceptance.
          </p>
        </div>
      </div>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Average Processing SLA</span>
          <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">1.8 Mins</h3>
          <span className="text-[11px] text-emerald-500 font-bold mt-2 block">85% faster vs legacy manual review</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Monthly Approval Rate</span>
          <h3 className="text-2xl font-extrabold text-emerald-400 mt-1">93.1%</h3>
          <span className="text-[11px] text-slate-400 font-medium mt-2 block">$14.2M total payout volume</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Fraud Detection Accuracy</span>
          <h3 className="text-2xl font-extrabold text-purple-400 mt-1">99.2%</h3>
          <span className="text-[11px] text-emerald-500 font-bold mt-2 block">$1.8M fraudulent payout prevented</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800">
          <span className="text-xs text-slate-400 font-medium">AI Recommendation Acceptance</span>
          <h3 className="text-2xl font-extrabold text-indigo-400 mt-1">96.4%</h3>
          <span className="text-[11px] text-slate-400 font-medium mt-2 block">Human-in-the-loop alignment</span>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Monthly Claims & Approval Volume */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-500" />
              <span>Monthly Volume & Approval Growth</span>
            </h3>
            <span className="text-xs text-slate-400">2026 YTD</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyTrends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="claims" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="approved" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SLA Distribution */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-purple-500" />
              <span>Processing Turnaround SLA Distribution</span>
            </h3>
            <span className="text-xs text-slate-400">Seconds to Verdict</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slaData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
