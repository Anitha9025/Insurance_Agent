'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  ShieldAlert,
  Sparkles,
  Plus,
  ChevronRight,
  Activity,
  Loader2
} from 'lucide-react';
import { MetricCard } from '@/components/ui/MetricCard';
import { StatusBadge, PriorityBadge } from '@/components/ui/StatusBadge';
import { useClaims } from '@/lib/context/ClaimsContext';
import { formatCurrency, formatDate } from '@/lib/utils';
import {
  fetchDashboardSummary,
  fetchDashboardCategoryBreakdown,
  fetchDashboardClaimVolume,
  fetchDashboardPriorityClaims,
  fetchDashboardAiMetrics
} from '@/lib/api';
import { Claim } from '@/types/insurance';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export default function DashboardPage() {
  const { claims, isLoading: isClaimsLoading } = useClaims();

  const [summary, setSummary] = useState<{
    total_claims: number;
    pending_claims: number;
    approved_claims: number;
    rejected_claims: number;
    emergency_claims: number;
  }>({
    total_claims: 0,
    pending_claims: 0,
    approved_claims: 0,
    rejected_claims: 0,
    emergency_claims: 0,
  });

  const [categoryBreakdown, setCategoryBreakdown] = useState<
    { category: string; count: number; percentage: number }[]
  >([]);

  const [claimVolume, setClaimVolume] = useState<{ date: string; count: number }[]>([]);
  const [priorityClaims, setPriorityClaims] = useState<Claim[]>([]);
  const [aiMetrics, setAiMetrics] = useState<{
    status: string;
    total_agent_steps: number;
    completed_agent_steps: number;
    evaluation_dataset_available: boolean;
    note: string;
  } | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        const [sumData, catData, volData, prioData, aiData] = await Promise.allSettled([
          fetchDashboardSummary(),
          fetchDashboardCategoryBreakdown(),
          fetchDashboardClaimVolume(),
          fetchDashboardPriorityClaims(),
          fetchDashboardAiMetrics(),
        ]);

        if (sumData.status === 'fulfilled') setSummary(sumData.value);
        if (catData.status === 'fulfilled') setCategoryBreakdown(catData.value.categories || []);
        if (volData.status === 'fulfilled') setClaimVolume(volData.value.volume || []);
        if (prioData.status === 'fulfilled') setPriorityClaims(prioData.value || []);
        if (aiData.status === 'fulfilled') setAiMetrics(aiData.value);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const CATEGORY_COLORS: Record<string, string> = {
    Vehicle: '#6366f1',
    Health: '#10b981',
    Home: '#8b5cf6',
    Travel: '#06b6d4',
    Business: '#f43f5e',
  };

  const recentClaims = priorityClaims.length > 0 ? priorityClaims : claims.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-3xl bg-gradient-to-r from-indigo-900/40 via-slate-900/80 to-purple-900/40 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1 z-10">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-[11px] font-bold uppercase tracking-wider">
              NexusClaim Dashboard
            </span>
            <span className="text-xs text-slate-400">Live PostgreSQL Data</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Insurance Officer Control Center
          </h1>
          <p className="text-xs text-slate-300">
            {summary.pending_claims > 0 ? (
              <>
                <span className="text-indigo-400 font-semibold">{summary.pending_claims} claims</span> require your review in the database.
              </>
            ) : (
              'All database claims are up to date.'
            )}
          </p>
        </div>

        <div className="flex items-center gap-3 z-10">
          <Link
            href="/claims/new"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>Register New Claim</span>
          </Link>
          <Link
            href="/copilot"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs transition-colors"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>AI Copilot Analysis</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Claims Intake"
          value={isLoading ? '...' : summary.total_claims.toLocaleString()}
          icon={FileText}
          trend="+Live DB"
          trendPositive={true}
          description="Total claims in PostgreSQL"
        />
        <MetricCard
          title="Pending / Under Review"
          value={isLoading ? '...' : summary.pending_claims.toLocaleString()}
          icon={Clock}
          trend="Action required"
          trendPositive={false}
          description="Claims awaiting review"
        />
        <MetricCard
          title="Approved Claims"
          value={isLoading ? '...' : summary.approved_claims.toLocaleString()}
          icon={CheckCircle2}
          trend="Finalized"
          trendPositive={true}
          description="Passed officer validation"
        />
        <MetricCard
          title="Rejected Claims"
          value={isLoading ? '...' : summary.rejected_claims.toLocaleString()}
          icon={XCircle}
          trend="Reviewed"
          trendPositive={false}
          description="Closed or rejected"
        />
      </div>

      {/* Main Content Grid: Charts & AI Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Claim Volume & Category Distribution */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim Volume Chart */}
          <div className="glass-panel p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-400" /> Claim Intake Volume Trend
                </h3>
                <p className="text-[11px] text-slate-400">Aggregated claim submissions over time</p>
              </div>
            </div>

            {claimVolume.length > 0 ? (
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={claimVolume} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="claimColor" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                    />
                    <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#claimColor)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-44 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-indigo-400" /> : 'Insufficient time-series data for chart analysis.'}
              </div>
            )}
          </div>

          {/* Category Distribution Breakdown */}
          <div className="glass-panel p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Activity className="w-4 h-4 text-purple-400" /> Insurance Category Distribution
            </h3>

            {categoryBreakdown.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryBreakdown}
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={70}
                        paddingAngle={4}
                        dataKey="count"
                        nameKey="category"
                      >
                        {categoryBreakdown.map((entry) => (
                          <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] || '#94a3b8'} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-2 text-xs">
                  {categoryBreakdown.map((cat) => (
                    <div key={cat.category} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: CATEGORY_COLORS[cat.category] || '#94a3b8' }}
                        />
                        <span className="text-slate-300 font-medium">{cat.category} Insurance</span>
                      </div>
                      <span className="font-mono text-white font-bold">{cat.count} ({cat.percentage}%)</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-indigo-400" /> : 'No category records present in database.'}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: AI Agent Operational Status Card */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-3xl bg-slate-900/80 border border-purple-500/20 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" /> AI Agent Operational Status
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 text-[10px] font-mono">
                Phase 5 Multi-Agent
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="text-xs text-slate-400 font-medium">Evaluation Status:</div>
              <div className="text-sm font-bold text-white">
                {aiMetrics?.status || 'Evaluation metrics not available'}
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500 block">Total Agent Steps:</span>
                  <span className="font-mono text-white font-bold">{aiMetrics?.total_agent_steps ?? 0}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Completed Steps:</span>
                  <span className="font-mono text-emerald-400 font-bold">{aiMetrics?.completed_agent_steps ?? 0}</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 pt-1">
                {aiMetrics?.note || 'Metrics are calculated strictly from PostgreSQL agent step logs without fabricated alignment rates.'}
              </div>
            </div>

            <Link
              href="/copilot"
              className="w-full py-2.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
            >
              <span>Launch Multi-Agent Analysis</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Priority Claims Table */}
      <div className="glass-panel p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-indigo-400" /> Recent Claims Requiring Attention
            </h3>
            <p className="text-xs text-slate-400">Live database records sorted by priority and date</p>
          </div>
          <Link
            href="/claims"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
          >
            <span>View All Claims ({claims.length})</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {recentClaims.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-3">Claim ID / Title</th>
                  <th className="py-3 px-3">Customer</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Claim Amount</th>
                  <th className="py-3 px-3">Priority</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentClaims.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-3">
                      <div className="font-bold text-white">{c.claimNumber}</div>
                      <div className="text-slate-400 truncate max-w-xs">{c.title}</div>
                    </td>
                    <td className="py-3 px-3 font-medium text-slate-200">
                      {c.customer?.name || 'Customer Pending'}
                    </td>
                    <td className="py-3 px-3 text-slate-300">{c.category}</td>
                    <td className="py-3 px-3 font-mono font-bold text-white">
                      {formatCurrency(c.claimAmount)}
                    </td>
                    <td className="py-3 px-3">
                      <PriorityBadge priority={c.priority} />
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/claims/${c.id}`}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 font-semibold transition-colors"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl text-xs text-slate-500">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin mx-auto text-indigo-400 mb-2" /> : 'No claims found in database.'}
          </div>
        )}
      </div>
    </div>
  );
}
