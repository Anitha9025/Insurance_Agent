'use client';

import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, ShieldQuestion, HelpCircle } from 'lucide-react';

interface FraudScoreCardProps {
  score?: number | null; // 0 to 100
  riskLevel?: string;
  signalCount?: number;
  explanation?: string;
}

export const FraudScoreCard: React.FC<FraudScoreCardProps> = ({ 
  score,
  riskLevel: customRiskLevel,
  signalCount = 0,
  explanation
}) => {
  const isAvailable = score !== null && score !== undefined;
  const numScore = isAvailable ? Number(score) : 0;

  let riskLevel = customRiskLevel || 'Low Risk';
  let badgeColor = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
  let gaugeColor = 'bg-emerald-500';
  let Icon = ShieldCheck;

  if (!isAvailable) {
    riskLevel = 'Unavailable';
    badgeColor = 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    gaugeColor = 'bg-slate-700';
    Icon = ShieldQuestion;
  } else if (numScore >= 40 && numScore < 70) {
    riskLevel = 'Moderate Risk';
    badgeColor = 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    gaugeColor = 'bg-amber-500';
    Icon = AlertTriangle;
  } else if (numScore >= 70) {
    riskLevel = 'High Fraud Alert';
    badgeColor = 'text-rose-500 bg-rose-500/10 border-rose-500/20';
    gaugeColor = 'bg-rose-500';
    Icon = ShieldAlert;
  }

  return (
    <div className="glass-panel p-4 rounded-xl border flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${!isAvailable ? 'text-slate-400' : numScore >= 70 ? 'text-rose-500 animate-pulse' : numScore >= 40 ? 'text-amber-500' : 'text-emerald-500'}`} />
          <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Composite Fraud Risk</span>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeColor}`}>
          {riskLevel.toUpperCase()}
        </span>
      </div>

      <div className="mt-3">
        <div className="flex items-baseline justify-between">
          {isAvailable ? (
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white">
              {numScore.toFixed(1)} <span className="text-xs font-normal text-slate-400">/ 100</span>
            </span>
          ) : (
            <span className="text-base font-bold text-slate-400">Pending / Unavailable</span>
          )}
          <span className="text-[11px] text-slate-500 font-medium">
            {signalCount} Signal{signalCount === 1 ? '' : 's'} Triggered
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full mt-2 overflow-hidden relative">
          <div
            className={`h-full rounded-full transition-all duration-700 ${gaugeColor}`}
            style={{ width: `${isAvailable ? numScore : 0}%` }}
          ></div>
        </div>

        <p className="text-[10px] text-slate-400 mt-2 leading-tight italic">
          {explanation || (isAvailable 
            ? "AI-assisted risk assessment. No configured fraud-risk signals were triggered in this analysis. This is not a definitive fraud determination."
            : "Fraud detection workflow has not been executed for this claim.")}
        </p>
      </div>
    </div>
  );
};

export const ConfidenceMeter: React.FC<{ score?: number | null; type?: string }> = ({ score }) => {
  const isAvailable = score !== null && score !== undefined && score > 0;
  const numScore = isAvailable ? Number(score) : 0;

  return (
    <div className="glass-panel p-4 rounded-xl border flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-700 dark:text-slate-200">AI Verdict Confidence</span>
        <span className={`text-xs font-bold ${isAvailable ? 'text-indigo-400' : 'text-slate-400'}`}>
          {isAvailable ? `${numScore.toFixed(1)}%` : 'Unavailable'}
        </span>
      </div>

      <div className="mt-3">
        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden relative">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              isAvailable ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500' : 'bg-slate-700'
            }`}
            style={{ width: `${isAvailable ? numScore : 0}%` }}
          ></div>
        </div>
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
          {isAvailable
            ? (numScore >= 90 ? 'High Confidence (Verified against policy & evidence)' : 'Moderate Confidence (Manual Officer review advised)')
            : 'Overall confidence: Unavailable (No calibrated statistical metric calculated)'}
        </p>
      </div>
    </div>
  );
};

