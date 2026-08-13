'use client';

import React from 'react';
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
  ArrowUpRight, 
  Plus,
  Users,
  Activity,
  Zap,
  ChevronRight
} from 'lucide-react';
import { MetricCard } from '@/components/ui/MetricCard';
import { StatusBadge, PriorityBadge } from '@/components/ui/StatusBadge';
import { useClaims } from '@/lib/context/ClaimsContext';
import { formatCurrency, formatDate } from '@/lib/utils';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

const dailyData = [
  { day: 'Mon', claims: 45, approved: 38, fraud: 2 },
  { day: 'Tue', claims: 52, approved: 44, fraud: 3 },
  { day: 'Wed', claims: 68, approved: 60, fraud: 1 },
  { day: 'Thu', claims: 61, approved: 52, fraud: 4 },
  { day: 'Fri', claims: 74, approved: 65, fraud: 2 },
  { day: 'Sat', claims: 30, approved: 26, fraud: 0 },
  { day: 'Sun', claims: 22, approved: 19, fraud: 1 },
];

const categoryData = [
  { name: 'Vehicle', value: 42, color: '#6366f1' },
  { name: 'Health', value: 28, color: '#10b981' },
  { name: 'Home', value: 16, color: '#8b5cf6' },
  { name: 'Travel', value: 9, color: '#06b6d4' },
  { name: 'Business', value: 5, color: '#f43f5e' },
];

const officerPerformance = [
  { name: 'Sarah Jenkins', reviewed: 142, accuracy: '98.2%', avgTime: '4.2m' },
  { name: 'Marcus Sterling', reviewed: 128, accuracy: '97.5%', avgTime: '5.1m' },
  { name: 'Michael Thorne', reviewed: 98, accuracy: '99.1%', avgTime: '6.8m' },
  { name: 'Elena Rostova', reviewed: 84, accuracy: '96.8%', avgTime: '4.8m' },
];

export default function DashboardPage() {
  const { claims, auditLogs } = useClaims();

  const totalClaimsCount = claims.length + 1240;
  const pendingCount = claims.filter(c => c.status === 'Submitted' || c.status === 'Draft').length + 38;
  const approvedCount = claims.filter(c => c.status === 'Approved').length + 1080;
  const rejectedCount = claims.filter(c => c.status === 'Rejected').length + 76;
  const underReviewCount = claims.filter(c => c.status === 'Under Review' || c.status === 'Requires Documents').length + 42;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-3xl bg-gradient-to-r from-indigo-900/40 via-slate-900/80 to-purple-900/40 border border-indigo-500/20 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1 z-10">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-[11px] font-bold uppercase tracking-wider">
              Officer Operations Hub
            </span>
            <span className="text-xs text-slate-400">August 6, 2026</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Welcome back, Officer Sarah Jenkins
          </h1>
          <p className="text-xs text-slate-300">
            Multi-Agent AI Copilot is online. <span className="text-indigo-400 font-semibold">12 claims</span> require your review today.
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
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs transition-all"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>Open AI Copilot</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Claims"
          value={totalClaimsCount.toLocaleString()}
          change="+12.4% vs last week"
          icon={FileText}
          iconColor="text-indigo-500"
          subtitle="Lifetime Intake"
        />
        <MetricCard
          title="Pending Claims"
          value={pendingCount}
          change="-4.2% queue time"
          icon={Clock}
          iconColor="text-amber-500"
          subtitle="Awaiting Processing"
        />
        <MetricCard
          title="Approved Claims"
          value={approvedCount.toLocaleString()}
          change="+8.9% payout rate"
          icon={CheckCircle2}
          iconColor="text-emerald-500"
          subtitle="94.2% Auto Confidence"
        />
        <MetricCard
          title="Rejected Claims"
          value={rejectedCount}
          change="0.8% fraud flagged"
          isPositive={false}
          icon={XCircle}
          iconColor="text-rose-500"
          subtitle="Arson & Duplicate"
        />
        <MetricCard
          title="Under Review"
          value={underReviewCount}
          change="Officer Decision Needed"
          icon={AlertTriangle}
          iconColor="text-purple-500"
          subtitle="Split Screen Hub"
        />
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Claim Volume Trend Chart */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-500" />
                <span>Weekly Claim Intake & Approval Volume</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Daily breakdown of total intake vs AI-recommended approvals.</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-medium">
              <span className="flex items-center gap-1 text-indigo-500"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block"></span> Intake</span>
              <span className="flex items-center gap-1 text-emerald-500"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span> Approved</span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorIntake" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorApproved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="claims" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorIntake)" />
                <Area type="monotone" dataKey="approved" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorApproved)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Claim Category Distribution Donut Chart */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center justify-between">
              <span>Category Breakdown</span>
              <span className="text-[11px] font-normal text-slate-500">Distribution %</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Claims by policy insurance sector.</p>
          </div>

          <div className="h-44 w-full relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-lg font-extrabold text-slate-900 dark:text-white">100%</span>
              <span className="text-[10px] text-slate-400">5 Categories</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-200/60 dark:border-slate-800">
            {categoryData.map((cat) => (
              <div key={cat.name} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }}></span>
                <span className="text-slate-600 dark:text-slate-300 font-medium">{cat.name}</span>
                <span className="text-slate-400 text-[10px] ml-auto font-bold">{cat.value}%</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Recent Claims Feed & AI Copilot Accuracy Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column: Recent Claims Table View */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-500" />
                <span>Recent Priority Claims</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Claims requiring immediate human-in-the-loop decision.</p>
            </div>
            <Link
              href="/claims"
              className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
            >
              <span>View All Claims</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-3">Claim ID</th>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Amount</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/60">
                {claims.slice(0, 4).map((claim) => (
                  <tr key={claim.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-900/60 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-indigo-600 dark:text-indigo-400">
                      {claim.claimNumber}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-semibold text-slate-900 dark:text-white">{claim.customer.name}</div>
                      <div className="text-[10px] text-slate-400">{claim.customer.email}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300 font-medium">
                      {claim.category}
                    </td>
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-white">
                      {formatCurrency(claim.claimAmount)}
                    </td>
                    <td className="py-3 px-3">
                      <PriorityBadge priority={claim.priority} />
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/claims/${claim.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 font-semibold text-[11px] transition-colors"
                      >
                        <span>Inspect</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: AI Recommendation Engine Stats & Officer Leaderboard */}
        <div className="space-y-6">
          {/* AI Accuracy Card */}
          <div className="glass-panel p-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/40 to-purple-950/30 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h4 className="font-bold text-xs text-white uppercase tracking-wider">AI Copilot Accuracy</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold border border-emerald-500/30">
                96.4% Benchmark
              </span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">96.4%</span>
              <span className="text-xs text-slate-300">Human Alignment Rate</span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Based on 1,480 claims evaluated this month. 96.4% of AI verdicts were accepted by senior human adjusters without modification.
            </p>

            <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-indigo-500/20">
              <span>LangMem Graph Nodes: <strong className="text-slate-200">14,290</strong></span>
              <span>Avg SLA: <strong className="text-emerald-400">1.8 mins</strong></span>
            </div>
          </div>

          {/* Officer Throughput */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
            <h4 className="font-bold text-xs text-slate-900 dark:text-white uppercase tracking-wider flex items-center justify-between">
              <span>Officer Performance</span>
              <Users className="w-3.5 h-3.5 text-slate-400" />
            </h4>

            <div className="space-y-2.5">
              {officerPerformance.map((officer) => (
                <div key={officer.name} className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 dark:bg-slate-900/60">
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">{officer.name}</span>
                    <span className="block text-[10px] text-slate-400">{officer.reviewed} claims reviewed</span>
                  </div>
                  <div className="text-right">
                    <span className="font-mono font-bold text-emerald-500">{officer.accuracy}</span>
                    <span className="block text-[10px] text-slate-400">Avg {officer.avgTime}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
