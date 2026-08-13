import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
}

export function getStatusBadgeStyle(status: string) {
  switch (status) {
    case 'Approved':
      return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 dark:bg-emerald-500/20 dark:text-emerald-400';
    case 'Under Review':
    case 'Processing':
    case 'Submitted':
      return 'bg-amber-500/10 text-amber-500 border-amber-500/20 dark:bg-amber-500/20 dark:text-amber-400';
    case 'Rejected':
      return 'bg-rose-500/10 text-rose-500 border-rose-500/20 dark:bg-rose-500/20 dark:text-rose-400';
    case 'Requires Documents':
    case 'Draft':
      return 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20 dark:bg-indigo-500/20 dark:text-indigo-400';
    default:
      return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
  }
}

export function getPriorityBadgeStyle(priority: string) {
  switch (priority) {
    case 'Emergency':
      return 'bg-rose-600 text-white font-semibold shadow-sm animate-pulse';
    case 'High':
      return 'bg-rose-500/15 text-rose-500 border-rose-500/30';
    case 'Medium':
      return 'bg-amber-500/15 text-amber-500 border-amber-500/30';
    case 'Low':
      return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    default:
      return 'bg-slate-500/15 text-slate-400';
  }
}
