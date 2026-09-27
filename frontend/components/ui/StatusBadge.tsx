'use client';

import React from 'react';
import { getStatusBadgeStyle, getPriorityBadgeStyle } from '@/lib/utils';
import { ClaimStatus, ClaimPriority } from '@/types/insurance';

export const StatusBadge: React.FC<{ status: ClaimStatus; className?: string }> = ({ status, className }) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getStatusBadgeStyle(
        status
      )} ${className || ''}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      <span>{status}</span>
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: ClaimPriority; className?: string }> = ({ priority, className }) => {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border uppercase tracking-wider ${getPriorityBadgeStyle(
        priority
      )} ${className || ''}`}
    >
      {priority}
    </span>
  );
};
