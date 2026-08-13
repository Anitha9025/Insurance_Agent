'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  CheckCircle2, 
  Loader2, 
  Sparkles, 
  ShieldCheck, 
  BrainCircuit, 
  BookOpen, 
  FileCheck, 
  ArrowRight,
  Zap,
  Activity
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';

const steps = [
  {
    title: 'Customer Verification',
    agent: 'Intake Agent',
    description: 'Validating SSN-XXX-XX-4891 against Enterprise Master Customer Registry...',
    icon: ShieldCheck,
    durationMs: 400
  },
  {
    title: 'Policy Retrieval & Limits Check',
    agent: 'Policy Validation Agent',
    description: 'Retrieving POL-AUTO-99824 active window & checking $50,000 coverage limit...',
    icon: FileCheck,
    durationMs: 450
  },
  {
    title: 'OCR Data Extraction & Analysis',
    agent: 'Claim History Agent',
    description: 'Extracting police report PA-8841 and Apex Auto estimate line items...',
    icon: Activity,
    durationMs: 600
  },
  {
    title: 'LangMem Memory Vector Lookup',
    agent: 'Memory Agent (LangMem)',
    description: 'Querying vector memory graph for historical subrogation & collision cases...',
    icon: BrainCircuit,
    durationMs: 700
  },
  {
    title: 'RAG Knowledge Policy Search',
    agent: 'RAG Knowledge Search',
    description: 'Searching master policy Section 4.2B & Subrogation Recourse clauses...',
    icon: BookOpen,
    durationMs: 650
  },
  {
    title: 'Fraud Risk Detection Engine',
    agent: 'Fraud Detection Agent',
    description: 'Running multi-factor risk model (Metadata, Timestamp, Geographic anomalies)...',
    icon: ShieldCheck,
    durationMs: 800
  },
  {
    title: 'AI Recommendation Synthesis',
    agent: 'Recommendation Agent',
    description: 'Synthesizing payout verdict, subrogation advice & confidence metrics...',
    icon: Sparkles,
    durationMs: 750
  }
];

export default function AIProcessingPage() {
  const router = useRouter();
  const { activeClaim } = useClaims();
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [isFinished, setIsFinished] = useState(false);

  useEffect(() => {
    let current = 0;
    const runNextStep = () => {
      if (current < steps.length) {
        setActiveStepIndex(current);
        const timer = setTimeout(() => {
          setCompletedSteps((prev) => [...prev, current]);
          current++;
          if (current < steps.length) {
            runNextStep();
          } else {
            setIsFinished(true);
          }
        }, steps[current].durationMs);
        return () => clearTimeout(timer);
      }
    };

    runNextStep();
  }, []);

  const handleProceedToClaimDetails = () => {
    const claimId = activeClaim?.id || 'claim-101';
    router.push(`/claims/${claimId}`);
  };

  const progressPercent = Math.round(((completedSteps.length) / steps.length) * 100);

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-6">
      {/* Header Visualizer */}
      <div className="glass-panel p-8 rounded-3xl bg-gradient-to-r from-indigo-950/80 via-slate-900 to-purple-950/80 border border-indigo-500/30 shadow-2xl relative overflow-hidden text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-wider border border-indigo-500/30">
          <Zap className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <span>Agentic Swarm Pipeline Active</span>
        </div>

        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Generating AI Recommendation & Verdict
        </h1>
        <p className="text-xs text-slate-300 max-w-xl mx-auto">
          Executing multi-agent workflow for <span className="text-indigo-400 font-mono font-bold">{activeClaim?.claimNumber || 'CLM-2026-8841'}</span>. OCR, LangMem vector search, and RAG knowledge match in progress.
        </p>

        {/* Progress Bar */}
        <div className="max-w-md mx-auto space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-slate-300">
            <span>Swarm Progress</span>
            <span className="text-indigo-400 font-mono">{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800 relative">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 transition-all duration-500 rounded-full"
              style={{ width: `${progressPercent}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Workflow Execution Stepper Cards */}
      <div className="space-y-3">
        {steps.map((step, idx) => {
          const isDone = completedSteps.includes(idx);
          const isCurrent = activeStepIndex === idx && !isDone;
          const Icon = step.icon;

          return (
            <div
              key={idx}
              className={`p-4 rounded-2xl border transition-all duration-300 flex items-center justify-between ${
                isDone
                  ? 'bg-slate-900/90 border-emerald-500/30 shadow-sm'
                  : isCurrent
                  ? 'bg-indigo-950/40 border-indigo-500/50 shadow-lg shadow-indigo-500/10 scale-[1.01]'
                  : 'bg-slate-900/40 border-slate-800/60 opacity-50'
              }`}
            >
              <div className="flex items-center gap-4">
                {/* Icon Status Indicator */}
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs transition-colors ${
                    isDone
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : isCurrent
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 animate-pulse'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-bold text-white">{step.title}</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                      {step.agent}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">{step.description}</p>
                </div>
              </div>

              <div className="text-right">
                {isDone ? (
                  <span className="text-[11px] font-bold text-emerald-400 font-mono flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Done ({step.durationMs}ms)
                  </span>
                ) : isCurrent ? (
                  <span className="text-[11px] font-bold text-indigo-400 font-mono animate-pulse">
                    Executing...
                  </span>
                ) : (
                  <span className="text-[11px] text-slate-600 font-mono">Queued</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Completion Action Banner */}
      {isFinished && (
        <div className="glass-panel p-6 rounded-3xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/40 via-slate-900 to-indigo-950/40 flex items-center justify-between animate-in fade-in duration-500">
          <div>
            <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span>Multi-Agent Evaluation Finished!</span>
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Recommendation generated with <strong className="text-emerald-400">94.8% Confidence Score</strong>. Ready for Officer review.
            </p>
          </div>

          <button
            onClick={handleProceedToClaimDetails}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-extrabold text-xs shadow-xl shadow-emerald-500/20 transition-all hover:scale-[1.03]"
          >
            <span>Review Claim Recommendation</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
