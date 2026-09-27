'use client';

import React, { useState } from 'react';
import {
  Bot,
  Sparkles,
  User,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ShieldQuestion,
  RefreshCw,
  Play,
  Loader2,
  FileText,
  AlertCircle,
  BookOpen,
  BrainCircuit,
  Database,
  Activity,
  Layers,
  Flag,
  ClipboardList,
  ListChecks,
  Info,
  TrendingUp,
  Eye,
  XCircle
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { analyzeClaimWorkflow } from '@/lib/api';
import { StatusBadge, PriorityBadge } from '@/components/ui/StatusBadge';

// ── Helpers ───────────────────────────────────────────────────────────────────

function RiskLevelBadge({ level }: { level: string }) {
  const cfg: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    low:     { color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', icon: <ShieldCheck className="w-3.5 h-3.5" />, label: 'LOW RISK' },
    medium:  { color: 'bg-amber-500/15 text-amber-400 border-amber-500/30',       icon: <ShieldAlert className="w-3.5 h-3.5" />,   label: 'MEDIUM RISK' },
    high:     { color: 'bg-rose-500/15 text-rose-400 border-rose-500/30',           icon: <ShieldX className="w-3.5 h-3.5" />,       label: 'HIGH RISK' },
    critical: { color: 'bg-red-600/20 text-red-400 border-red-500/40',              icon: <ShieldX className="w-3.5 h-3.5 animate-pulse" />, label: 'CRITICAL RISK' },
    unknown: { color: 'bg-slate-500/15 text-slate-400 border-slate-500/30',        icon: <ShieldQuestion className="w-3.5 h-3.5" />, label: 'UNKNOWN' },
  };
  const c = cfg[level?.toLowerCase()] || cfg.unknown;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border ${c.color}`}>
      {c.icon} {c.label}
    </span>
  );
}

function RecommendationBadge({ rec }: { rec: string }) {
  const cfg: Record<string, { color: string; label: string }> = {
    approve_recommended:      { color: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: '✓ Approve Recommended' },
    reject_recommended:       { color: 'bg-rose-500/15 text-rose-400 border-rose-500/30',           label: '✗ Reject Recommended' },
    request_more_information: { color: 'bg-amber-500/15 text-amber-400 border-amber-500/30',        label: '⚠ Request More Info' },
    manual_review_required:   { color: 'bg-orange-500/15 text-orange-400 border-orange-500/30',     label: '👁 Manual Review Required' },
    insufficient_evidence:    { color: 'bg-slate-500/15 text-slate-400 border-slate-500/30',        label: '? Insufficient Evidence' },
    processing_failed:        { color: 'bg-rose-500/15 text-rose-400 border-rose-500/30',           label: '⊘ Processing Failed' },
  };
  const c = cfg[rec] || { color: 'bg-slate-500/15 text-slate-400 border-slate-500/30', label: rec };
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${c.color}`}>
      {c.label}
    </span>
  );
}

function EvidenceCategoryBadge({ cat }: { cat: string }) {
  const cfg: Record<string, string> = {
    observed: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    inferred: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
    unknown:  'bg-slate-500/15 text-slate-400 border-slate-500/30',
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${cfg[cat] || cfg.unknown}`}>
      {cat}
    </span>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const cfg: Record<string, string> = {
    info:   'bg-slate-500',
    low:    'bg-emerald-500',
    medium: 'bg-amber-500',
    high:   'bg-rose-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${cfg[severity] || cfg.info}`} />;
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 45 ? 'bg-rose-500' : pct >= 20 ? 'bg-amber-500' : 'bg-emerald-500';
  return (
    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
      <div className={`h-2 rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AICopilotPage() {
  const { claims, activeClaim } = useClaims();
  const [selectedClaimId, setSelectedClaimId] = useState<string>(activeClaim?.id || (claims[0]?.id || ''));
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [workflowState, setWorkflowState] = useState<any | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const currentClaim = claims.find((c) => c.id === selectedClaimId) || claims[0];

  React.useEffect(() => {
    let isMounted = true;
    async function loadAnalysis() {
      if (selectedClaimId) {
        try {
          const { fetchClaimAnalysis } = await import('@/lib/api');
          const analysis = await fetchClaimAnalysis(selectedClaimId).catch(() => null);
          if (isMounted && analysis && analysis.workflow_status === 'completed') {
            setWorkflowState({
              workflowStatus: 'completed',
              completedAgents: ['Claim Intake Agent', 'Customer Verification Agent', 'Document Analysis Agent', 'Policy Validation Agent', 'Claim History Agent', 'RAG Knowledge Agent', 'Memory Agent', 'Evidence Normalization Agent', 'Fraud Detection Agent', 'Recommendation Agent'],
              dbToolCalls: [{ toolName: 'get_claim_by_id' }, { toolName: 'get_customer_by_id' }, { toolName: 'get_policy_by_number' }],
              fraudAssessment: analysis.fraud_assessment,
              recommendation: analysis.recommendation,
              normalizedEvidence: analysis.recommendation?.supporting_evidence ? analysis.recommendation.supporting_evidence.map((s: string, i: number) => ({
                id: `ev-${i}`,
                sourceAgent: 'Analysis Engine',
                category: 'observed',
                severity: 'medium',
                description: s
              })) : []
            });
          }
        } catch (err) {
          console.warn('Could not load analysis for selected claim:', err);
        }
      }
    }
    loadAnalysis();
    return () => { isMounted = false; };
  }, [selectedClaimId]);

  const handleRunAnalysis = async () => {
    if (!currentClaim) return;
    setIsAnalyzing(true);
    setAnalysisError(null);
    setWorkflowState(null);
    try {
      const result = await analyzeClaimWorkflow(currentClaim.id);
      setWorkflowState(result);
    } catch (err: any) {
      console.error('Error running workflow analysis:', err);
      setAnalysisError(err.message || 'Failed to execute multi-agent workflow on backend.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fraud = workflowState?.fraudAssessment || workflowState?.fraud_assessment;
  const rec   = workflowState?.recommendation;
  const evidence = workflowState?.normalizedEvidence || workflowState?.normalized_evidence || [];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">

      {/* ── Header ── */}
      <div className="glass-panel p-6 rounded-3xl bg-gradient-to-r from-purple-900/40 via-slate-900/80 to-indigo-900/40 border border-purple-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-bold uppercase tracking-wider">
              Phase 7 · Fraud Detection + Recommendation Engine
            </span>
            <span className="text-xs text-slate-400">Full 10-Agent Swarm</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Bot className="w-6 h-6 text-purple-400" /> AI Copilot · Evidence-Based Claim Analysis
          </h1>
          <p className="text-xs text-slate-300">
            Runs all 10 agents: Intake → Customer → Document → Policy → History → RAG → Memory → Evidence Normalization → Fraud Detection → Recommendation.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {claims.length > 0 ? (
            <select
              value={selectedClaimId}
              onChange={(e) => { setSelectedClaimId(e.target.value); setWorkflowState(null); }}
              className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
            >
              {claims.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.claimNumber} — {c.category} (${c.claimAmount.toLocaleString()})
                </option>
              ))}
            </select>
          ) : (
            <div className="text-xs text-slate-500 italic">No claims in database</div>
          )}

          <button
            id="run-swarm-analysis-btn"
            onClick={handleRunAnalysis}
            disabled={isAnalyzing || !currentClaim}
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs shadow-lg shadow-purple-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.02]"
          >
            {isAnalyzing ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Running 10-Agent Swarm…</>
            ) : (
              <><Play className="w-4 h-4" /> Run Full Analysis</>
            )}
          </button>
        </div>
      </div>

      {/* ── Error Alert ── */}
      {analysisError && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{analysisError}</span>
        </div>
      )}

      {/* ── Results Workspace ── */}
      {workflowState ? (
        <div className="space-y-8">

          {/* Workflow Status Banner */}
          <div className="glass-panel p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs flex-wrap gap-3">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-bold text-slate-400">Workflow Status:</span>
              <span className={`px-2.5 py-1 rounded-full font-bold text-[11px] uppercase ${
                workflowState.workflowStatus === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}>
                {workflowState.workflowStatus}
              </span>
            </div>
            <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
              <span>Agents Run: <strong className="text-white">{workflowState.completedAgents?.length || 0}</strong></span>
              <span>DB Tool Calls: <strong className="text-purple-400">{workflowState.dbToolCalls?.length || 0}</strong></span>
              <span>Evidence Items: <strong className="text-blue-400">{evidence.length}</strong></span>
            </div>
          </div>

          {/* Phase 1–6 Results Grid */}
          <div>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Layers className="w-3.5 h-3.5" /> Phase 1–6 Agent Results
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

              {/* DB Tools Log */}
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <Database className="w-4 h-4 text-indigo-400" /> Controlled DB Tools
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">Read-Only</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  {workflowState.dbToolCalls?.length > 0 ? workflowState.dbToolCalls.map((t: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] flex justify-between items-center text-slate-300">
                      <span>{t.tool_name || t.toolName}</span>
                      <span className="text-emerald-400 font-bold">✓</span>
                    </div>
                  )) : <p className="text-slate-500 text-[11px]">No tool calls recorded.</p>}
                </div>
              </div>

              {/* RAG Knowledge */}
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-purple-400" /> RAG Knowledge Agent
                  </h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                    workflowState.ragAnalysis?.is_grounded
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    Confidence: {workflowState.ragAnalysis?.confidence || 0}%
                  </span>
                </div>
                <p className="text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] leading-relaxed">
                  {workflowState.ragAnalysis?.answer || 'Policy knowledge analysis complete.'}
                </p>
                <div className="text-[11px] text-purple-300">
                  {workflowState.ragAnalysis?.citations?.length || 0} policy chunk(s) applied
                </div>
              </div>

              {/* Memory Agent */}
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <BrainCircuit className="w-4 h-4 text-teal-400" /> Memory Agent
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-500/10 text-teal-300 border border-teal-500/20">
                    {workflowState.retrievedMemories?.similar_claims_count || 0} precedents
                  </span>
                </div>
                <p className="text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-[11px] leading-relaxed">
                  {workflowState.retrievedMemories?.summary || 'No matching prior claim precedents found.'}
                </p>
              </div>

              {/* Customer Verification */}
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <User className="w-4 h-4 text-purple-400" /> Customer Verification
                  </h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                    workflowState.customerVerification?.verified
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {workflowState.customerVerification?.verified ? 'Verified' : 'Needs Review'}
                  </span>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Risk Score:</span>
                    <span className="font-mono text-white font-bold">{workflowState.customerVerification?.riskScore ?? '—'}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Matched Fields:</span>
                    <span className="font-mono text-emerald-400">{workflowState.customerVerification?.matchedFields?.length || 0} verified</span>
                  </div>
                </div>
              </div>

              {/* Document Analysis */}
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 md:col-span-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-400" /> Document Analysis Agent (Vision AI)
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {workflowState.documentAnalysis?.documentsAnalyzed ?? 0} docs analyzed
                  </span>
                </div>
                {workflowState.documentAnalysis?.hasFlaggedDocuments && (
                  <div className="flex items-center gap-2 text-amber-400 text-xs bg-amber-500/10 rounded-lg px-3 py-2 border border-amber-500/20">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" /> One or more documents flagged for review.
                  </div>
                )}
                {workflowState.documentAnalysis?.evidence?.slice(0, 3).map((ev: string, i: number) => (
                  <p key={i} className="text-[11px] text-slate-400 leading-relaxed">{ev}</p>
                ))}
              </div>
            </div>
          </div>

          {/* ── PHASE 7 ─────────────────────────────────────────────────────── */}
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-rose-400" /> Phase 7 · Fraud Detection + Recommendation
              </h2>
              <div className="flex-1 h-px bg-gradient-to-r from-rose-500/30 to-transparent" />
            </div>

            {/* ── Evidence Normalization Summary ── */}
            {evidence.length > 0 && (
              <div className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-xs font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-blue-400" /> Normalized Evidence Items
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20">
                    {evidence.length} items
                  </span>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {evidence.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
                      <SeverityDot severity={item.severity || item.severityLevel || 'info'} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-0.5">
                          <EvidenceCategoryBadge cat={item.category} />
                          <span className="text-[10px] text-slate-500">{item.source_agent || item.sourceAgent}</span>
                        </div>
                        <p className="text-[11px] text-slate-300 leading-relaxed">{item.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Fraud Risk Assessment ── */}
            {fraud ? (
              <div className="glass-panel p-5 rounded-2xl bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-rose-950/20 border border-rose-500/20 space-y-5">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-rose-400" /> Fraud Risk Assessment
                  </h3>
                  <RiskLevelBadge level={fraud.risk_level || fraud.riskLevel || 'unknown'} />
                </div>

                {/* Score Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400 font-medium">Composite Risk Indicator Score</span>
                    <span className="font-mono font-bold text-white">{(fraud.rule_based_score ?? fraud.ruleBasedScore ?? 0).toFixed(1)} / 100</span>
                  </div>
                  <ScoreBar score={fraud.rule_based_score ?? fraud.ruleBasedScore ?? 0} />
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>Score Rule Version: {fraud.score_rule_version || fraud.scoreRuleVersion || 'v1.0'}</span>
                    <span>{fraud.signals_triggered ?? fraud.signal_count ?? (fraud.signals || fraud.signals_json || fraud.signalsJson || []).length} signal(s) triggered</span>
                  </div>
                </div>

                {/* Signals */}
                {(fraud.signals || fraud.signals_json || fraud.signalsJson || []).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">Risk Signals</p>
                    <div className="space-y-2">
                      {(fraud.signals || fraud.signals_json || fraud.signalsJson || []).map((sig: any, idx: number) => (
                        <div key={idx} className={`flex items-start gap-3 p-3 rounded-xl border ${
                          sig.severity === 'high' ? 'bg-rose-500/8 border-rose-500/20' :
                          sig.severity === 'medium' ? 'bg-amber-500/8 border-amber-500/20' :
                          'bg-slate-800/50 border-slate-700'
                        }`}>
                          <Flag className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${
                            sig.severity === 'high' ? 'text-rose-400' :
                            sig.severity === 'medium' ? 'text-amber-400' : 'text-slate-500'
                          }`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-[10px] font-bold text-slate-300 uppercase">{sig.signal_type?.replace(/_/g, ' ')}</span>
                              <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                                sig.severity === 'high' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
                                sig.severity === 'medium' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                                'bg-slate-600/20 text-slate-400 border-slate-600/30'
                              }`}>{sig.severity}</span>
                              <span className="text-[10px] text-slate-500">+{sig.score_contribution?.toFixed(1)} pts</span>
                            </div>
                            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">{sig.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Supporting / Contradictory */}
                {((fraud.supportingEvidence || fraud.supporting_evidence || fraud.supporting_evidence_json || []).length > 0 || (fraud.contradictoryEvidence || fraud.contradictory_evidence || fraud.contradictory_evidence_json || []).length > 0) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(fraud.supportingEvidence || fraud.supporting_evidence || fraud.supporting_evidence_json || []).length > 0 && (
                      <div className="space-y-1.5">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Supporting Risk Factors</p>
                        {(fraud.supportingEvidence || fraud.supporting_evidence || fraud.supporting_evidence_json || []).slice(0, 3).map((ev: string, i: number) => (
                          <p key={i} className="text-[11px] text-slate-400 leading-relaxed bg-slate-950/60 px-2.5 py-1.5 rounded border border-slate-800">{ev}</p>
                        ))}
                      </div>
                    )}
                    {(fraud.contradictoryEvidence || fraud.contradictory_evidence || fraud.contradictory_evidence_json || []).length > 0 && (
                      <div className="space-y-1.5">
                        <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest">Contradicting / Positive Factors</p>
                        {(fraud.contradictoryEvidence || fraud.contradictory_evidence || fraud.contradictory_evidence_json || []).slice(0, 3).map((ev: string, i: number) => (
                          <p key={i} className="text-[11px] text-emerald-300/70 leading-relaxed bg-emerald-950/30 px-2.5 py-1.5 rounded border border-emerald-500/20">{ev}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Disclaimer */}
                <div className="flex items-start gap-2 text-[11px] text-slate-500 bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2.5">
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
                  <span>{fraud.assessment_disclaimer || fraud.assessmentDisclaimer}</span>
                </div>
              </div>
            ) : (
              <div className="p-6 rounded-2xl border border-dashed border-rose-500/20 bg-rose-950/10 text-center text-xs text-rose-400/60">
                Fraud assessment not available — run analysis to generate.
              </div>
            )}

            {/* ── Recommendation Panel ── */}
            {rec ? (
              <div className="glass-panel p-5 rounded-2xl bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-indigo-950/20 border border-indigo-500/20 space-y-5">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <ClipboardList className="w-5 h-5 text-indigo-400" /> AI-Assisted Recommendation
                  </h3>
                  <RecommendationBadge rec={rec.recommendation} />
                </div>

                {/* Advisory Notice */}
                <div className="flex items-start gap-2 text-[11px] bg-indigo-950/40 border border-indigo-500/25 rounded-xl px-3 py-2.5 text-indigo-300">
                  <Eye className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span><strong>Advisory Only</strong> — This AI recommendation does not constitute a final decision. The insurance officer retains full authority.</span>
                </div>

                {/* Override */}
                {(rec.override_reason || rec.overrideReason) && (
                  <div className="flex items-start gap-2 text-[11px] bg-amber-950/30 border border-amber-500/25 rounded-xl px-3 py-2.5 text-amber-300">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span><strong>Override Applied:</strong> {rec.override_reason || rec.overrideReason}</span>
                  </div>
                )}

                {/* Reasoning */}
                <div className="space-y-2">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">Reasoning Summary</p>
                  <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 text-[12px] text-slate-300 leading-relaxed whitespace-pre-line">
                    {rec.reasoning_summary || rec.reasoningSummary}
                  </div>
                </div>

                {/* Required Actions */}
                {(rec.required_next_actions || rec.requiredNextActions || []).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                      <ListChecks className="w-3.5 h-3.5" /> Required Next Actions for Officer
                    </p>
                    <div className="space-y-1.5">
                      {(rec.required_next_actions || rec.requiredNextActions || []).map((action: string, i: number) => (
                        <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                          <ChevronRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                          <span className="text-[11px] text-slate-300">{action}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Policy References */}
                {(rec.policy_references || rec.policyReferences || []).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                      <BookOpen className="w-3.5 h-3.5" /> Policy References
                    </p>
                    {(rec.policy_references || rec.policyReferences || []).map((ref: string, i: number) => (
                      <p key={i} className="text-[11px] text-purple-300/80 bg-purple-950/20 px-3 py-2 rounded-lg border border-purple-500/15">{ref}</p>
                    ))}
                  </div>
                )}

                {/* Risk Summary */}
                {(rec.risk_summary || rec.riskSummary || []).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest">Risk Signal Summary</p>
                    {(rec.risk_summary || rec.riskSummary || []).map((r: string, i: number) => (
                      <p key={i} className="text-[11px] text-rose-300/70 leading-relaxed px-3 py-1.5 bg-rose-950/20 rounded border border-rose-500/15">{r}</p>
                    ))}
                  </div>
                )}

                {/* Disclaimer */}
                <div className="flex items-start gap-2 text-[11px] text-slate-500 bg-slate-950/50 border border-slate-800 rounded-xl px-3 py-2.5">
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{rec.officer_decision_disclaimer || rec.officerDecisionDisclaimer}</span>
                </div>
              </div>
            ) : (
              <div className="p-6 rounded-2xl border border-dashed border-indigo-500/20 bg-indigo-950/10 text-center text-xs text-indigo-400/60">
                Recommendation not available — run analysis to generate.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center border-2 border-dashed border-slate-800 rounded-3xl space-y-3">
          <Bot className="w-10 h-10 text-purple-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Ready for Full 10-Agent Swarm Analysis</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click <strong>"Run Full Analysis"</strong> to trigger the complete Phase 7 pipeline: all prior agents plus Evidence Normalization, Fraud Detection, and AI-assisted Recommendation for <strong>{currentClaim?.claimNumber || 'the selected claim'}</strong>.
          </p>
        </div>
      )}
    </div>
  );
}

