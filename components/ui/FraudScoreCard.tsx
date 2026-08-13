'use client';

import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

interface FraudScoreCardProps {
  score: number; // 0 to 100
}

export const FraudScoreCard: React.FC<FraudScoreCardProps> = ({ score }) => {
  let riskLevel = 'Low Risk';
  let badgeColor = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
  let gaugeColor = 'bg-emerald-500';
  let Icon = ShieldCheck;

  if (score >= 40 && score < 70) {
    riskLevel = 'Moderate Risk';
    badgeColor = 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    gaugeColor = 'bg-amber-500';
    Icon = AlertTriangle;
  } else if (score >= 70) {
    riskLevel = 'High Fraud Alert';
    badgeColor = 'text-rose-500 bg-rose-500/10 border-rose-500/20';
    gaugeColor = 'bg-rose-500';
    Icon = ShieldAlert;
  }

  return (
    <div className="glass-panel p-4 rounded-xl border flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${score >= 70 ? 'text-rose-500 animate-pulse' : score >= 40 ? 'text-amber-500' : 'text-emerald-500'}`} />
          <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Fraud Risk Index</span>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeColor}`}>
          {riskLevel}
        </span>
      </div>

      <div className="mt-3">
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-extrabold text-slate-900 dark:text-white">{score} <span className="text-xs font-normal text-slate-400">/ 100</span></span>
          <span className="text-[11px] text-slate-500 font-medium">AI Fraud Engine</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full mt-2 overflow-hidden relative">
          <div
            className={`h-full rounded-full transition-all duration-700 ${gaugeColor}`}
            style={{ width: `${score}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export const ConfidenceMeter: React.FC<{ score: number }> = ({ score }) => {
  return (
    <div className="glass-panel p-4 rounded-xl border flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-700 dark:text-slate-200">AI Verdict Confidence</span>
        <span className="text-xs font-bold text-indigo-500">{score.toFixed(1)}%</span>
      </div>

      <div className="mt-3">
        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden relative">
          <div
            className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 transition-all duration-700"
            style={{ width: `${score}%` }}
          ></div>
        </div>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
          {score >= 90 ? 'High Confidence (Verified against 4+ knowledge sources)' : 'Moderate Confidence (Manual Officer review advised)'}
        </p>
      </div>
    </div>
  );
};
