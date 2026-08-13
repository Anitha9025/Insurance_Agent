'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  FilePlus, 
  FileText, 
  Bot, 
  BookOpen, 
  BrainCircuit, 
  BarChart3, 
  ShieldCheck, 
  Settings,
  Sparkles,
  ChevronRight,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useClaims } from '@/lib/context/ClaimsContext';

const menuItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'New Claim', href: '/claims/new', icon: FilePlus, highlight: true },
  { name: 'Claims', href: '/claims', icon: FileText, badge: '5' },
  { name: 'AI Copilot', href: '/copilot', icon: Bot, isAi: true },
  { name: 'Knowledge Base', href: '/knowledge', icon: BookOpen },
  { name: 'Memory', href: '/memory', icon: BrainCircuit },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Audit Logs', href: '/audit-logs', icon: ShieldCheck },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/80 backdrop-blur-xl flex flex-col h-screen sticky top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform duration-200">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm text-slate-900 dark:text-white tracking-tight">NexusClaim</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-500 dark:bg-indigo-500/20 dark:text-indigo-400 border border-indigo-500/20">
                Enterprise
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Agentic AI Copilot</p>
          </div>
        </Link>
      </div>

      {/* Copilot Engine Status Pill */}
      <div className="px-4 py-3 mx-3 my-2 rounded-xl bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-teal-500/10 border border-indigo-500/20 dark:border-indigo-500/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="relative">
            <span className="w-2 h-2 rounded-full bg-emerald-500 block"></span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 absolute inset-0 animate-ping opacity-75"></span>
          </div>
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Multi-Agent V3 Active</span>
        </div>
        <Zap className="w-3.5 h-3.5 text-indigo-500" />
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150",
                isActive
                  ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/25 dark:bg-indigo-600"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-900/60",
                item.highlight && !isActive && "border border-indigo-500/30 text-indigo-600 dark:text-indigo-400 bg-indigo-500/5 hover:bg-indigo-500/10"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive
                      ? "text-white"
                      : item.isAi
                      ? "text-purple-500 dark:text-purple-400 group-hover:text-purple-600"
                      : "text-slate-500 dark:text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200"
                  )}
                />
                <span>{item.name}</span>
              </div>

              <div className="flex items-center gap-1.5">
                {item.badge && (
                  <span
                    className={cn(
                      "px-2 py-0.5 text-[10px] font-bold rounded-full",
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
                {item.isAi && !isActive && (
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* User Footer Profile */}
      <div className="p-3 border-t border-slate-200/80 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40">
        <div className="flex items-center justify-between p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 text-white font-bold text-xs flex items-center justify-center shadow-sm">
              SJ
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">Sarah Jenkins</p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">Senior Claim Officer</p>
            </div>
          </div>
          <Link href="/login" className="p-1 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors" title="Sign out">
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </aside>
  );
};
