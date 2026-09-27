'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Activity,
  CheckCircle2,
  Clock,
  PieChart as PieIcon,
  Sparkles,
  Loader2
} from 'lucide-react';
import {
  fetchDashboardSummary,
  fetchDashboardCategoryBreakdown,
  fetchDashboardClaimVolume,
  fetchDashboardAiMetrics
} from '@/lib/api';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<any>({
    total_claims: 0,
    pending_claims: 0,
    approved_claims: 0,
    rejected_claims: 0,
  });
  const [categories, setCategories] = useState<any[]>([]);
  const [volume, setVolume] = useState<any[]>([]);
  const [aiMetrics, setAiMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      setIsLoading(true);
      try {
        const [sumRes, catRes, volRes, aiRes] = await Promise.allSettled([
          fetchDashboardSummary(),
          fetchDashboardCategoryBreakdown(),
          fetchDashboardClaimVolume(),
          fetchDashboardAiMetrics(),
        ]);

        if (sumRes.status === 'fulfilled') setSummary(sumRes.value);
        if (catRes.status === 'fulfilled') setCategories(catRes.value.categories || []);
        if (volRes.status === 'fulfilled') setVolume(volRes.value.volume || []);
        if (aiRes.status === 'fulfilled') setAiMetrics(aiRes.value);
      } catch (err) {
        console.error('Analytics load error:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  const CATEGORY_COLORS: Record<string, string> = {
    Vehicle: '#6366f1',
    Health: '#10b981',
    Home: '#8b5cf6',
    Travel: '#06b6d4',
    Business: '#f43f5e',
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold uppercase tracking-wider">
              PostgreSQL BI Engine
            </span>
            <span className="text-xs text-slate-400">Live Database Analytics</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-1">
            Claims & Agentic Analytics Dashboard
          </h1>
          <p className="text-xs text-slate-400">
            Real-time business intelligence metrics computed directly from active database records without synthetic trends.
          </p>
        </div>
      </div>

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Total Registered Claims</span>
          <div className="text-2xl font-extrabold text-white font-mono">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : summary.total_claims}
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Pending Review</span>
          <div className="text-2xl font-extrabold text-amber-400 font-mono">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : summary.pending_claims}
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Approved Claims</span>
          <div className="text-2xl font-extrabold text-emerald-400 font-mono">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : summary.approved_claims}
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Agent Steps Logged</span>
          <div className="text-2xl font-extrabold text-purple-400 font-mono">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : (aiMetrics?.total_agent_steps ?? 0)}
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown Bar Chart */}
        <div className="glass-panel p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <PieIcon className="w-4 h-4 text-indigo-400" /> Category Distribution (PostgreSQL)
          </h3>
          {categories.length > 0 ? (
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categories} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="category" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                  <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-44 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-indigo-400" /> : 'No category records present in database.'}
            </div>
          )}
        </div>

        {/* Claim Intake Timeline Volume */}
        <div className="glass-panel p-6 rounded-3xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <TrendingUp className="w-4 h-4 text-emerald-400" /> Incident Date Intake Volume
          </h3>
          {volume.length > 0 ? (
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volume} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }} />
                  <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-44 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-indigo-400" /> : 'Insufficient data for timeline volume chart.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
