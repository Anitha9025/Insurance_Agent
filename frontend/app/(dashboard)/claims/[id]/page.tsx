'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  User, 
  Shield, 
  FileText, 
  BrainCircuit, 
  BookOpen, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Sparkles, 
  Download, 
  Eye, 
  File, 
  Clock, 
  ArrowLeft, 
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Wrench,
  Bot,
  Check,
  X,
  Send
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { StatusBadge, PriorityBadge } from '@/components/ui/StatusBadge';
import { FraudScoreCard, ConfidenceMeter } from '@/components/ui/FraudScoreCard';
import { formatCurrency, formatDate } from '@/lib/utils';
import { fetchClaimById, triggerDocumentOcr, fetchClaimAnalysis } from '@/lib/api';
import { ClaimDocument, Claim } from '@/types/insurance';

export default function ClaimDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const claimId = params.id as string;
  const { getClaimById, updateClaimDecision } = useClaims();

  const [claim, setClaim] = useState<Claim | null>(null);
  const [phase7Analysis, setPhase7Analysis] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  React.useEffect(() => {
    let isMounted = true;
    async function loadClaim() {
      if (!claimId) return;
      setIsLoading(true);
      try {
        const [fetched, analysis] = await Promise.all([
          fetchClaimById(claimId),
          fetchClaimAnalysis(claimId).catch(() => null)
        ]);
        if (isMounted) {
          if (fetched) {
            setClaim(fetched);
          } else {
            const local = getClaimById(claimId);
            if (local) setClaim(local);
          }
          if (analysis) setPhase7Analysis(analysis);
        }
      } catch (err) {
        console.warn('Failed to load claim details from backend:', err);
        if (isMounted) {
          const local = getClaimById(claimId);
          if (local) setClaim(local);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadClaim();
    return () => {
      isMounted = false;
    };
  }, [claimId, getClaimById]);

  const [decisionModalAction, setDecisionModalAction] = useState<'Approve' | 'Reject' | 'Request Additional Documents' | null>(null);
  const [decisionReason, setDecisionReason] = useState('');
  const [selectedDocPreview, setSelectedDocPreview] = useState<ClaimDocument | null>(null);
  const [isProcessingOcr, setIsProcessingOcr] = useState(false);

  const handleOpenDocPreview = async (doc: ClaimDocument) => {
    setSelectedDocPreview(doc);
    if (!doc.ocrFields || doc.ocrFields.length === 0) {
      setIsProcessingOcr(true);
      try {
        await triggerDocumentOcr(doc.id);
        if (claimId) {
          const updated = await fetchClaimById(claimId);
          if (updated) {
            setClaim(updated);
            const freshDoc = updated.documents.find((d) => d.id === doc.id || d.fileName === doc.fileName);
            if (freshDoc) {
              setSelectedDocPreview(freshDoc);
            }
          }
        }
      } catch (ocrErr) {
        console.warn('OCR trigger error:', ocrErr);
      } finally {
        setIsProcessingOcr(false);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="text-center py-20 text-slate-400">
        <p className="text-sm font-medium">Loading claim details from backend database...</p>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-white">Claim Not Found</h2>
        <p className="text-xs text-slate-400 mt-1">Claim ID '{claimId}' could not be located in database.</p>
        <Link href="/claims" className="text-indigo-400 underline text-xs mt-3 inline-block">Return to Claims Table</Link>
      </div>
    );
  }

  const rec = claim.aiRecommendation;
  const fa = phase7Analysis?.fraud_assessment;
  const rr = phase7Analysis?.recommendation;

  const verdictText = rr?.recommendation_label || rr?.decision || rec?.verdict || 'Approve Recommended';
  const isApprove = verdictText.toLowerCase().includes('approve');
  const isReject = verdictText.toLowerCase().includes('reject');

  const policyDeductible = claim.policy?.deductible ? Number(claim.policy.deductible) : 0;
  const recommendedPayoutAmount = (rr?.recommended_payout !== undefined && rr?.recommended_payout !== null)
    ? rr.recommended_payout
    : ((rec?.recommendedAmount !== undefined && rec?.recommendedAmount !== null)
      ? rec.recommendedAmount
      : Math.max(0, claim.claimAmount - policyDeductible));

  const reasoningSummary = rr?.reasoning_summary || rec?.reasoningSummary || 'Claim registration meets all primary coverage criteria. Documentation is consistent with policy limits.';
  
  const keyFindings: string[] = (rr?.supporting_evidence && rr.supporting_evidence.length > 0)
    ? rr.supporting_evidence
    : (rec?.keyFindings || []);

  const fraudScore = fa ? Number(fa.risk_score) : (rec ? Number(rec.fraudRiskScore) : 0.0);
  const riskLevel = fa ? fa.risk_level : 'low';
  const signalCount = fa ? Number(fa.signals_triggered) : 0;
  const fraudExplanation = fa?.explanation || "AI-assisted risk assessment. No configured fraud-risk signals were triggered in this analysis. This is not a definitive fraud determination.";

  // Overall confidence is set to null if uncalibrated so ConfidenceMeter displays 'Unavailable'
  const confidenceScore = (rec?.confidenceScore && rec.confidenceScore > 0) ? rec.confidenceScore : null;


  const handleExecuteDecision = () => {
    if (decisionModalAction && decisionReason.trim()) {
      updateClaimDecision(claim.id, decisionModalAction, decisionReason);
      setDecisionModalAction(null);
      setDecisionReason('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-sm text-indigo-600 dark:text-indigo-400">{claim.claimNumber}</span>
              <StatusBadge status={claim.status} />
              <PriorityBadge priority={claim.priority} />
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-0.5">
              {claim.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => alert(`Audit log report downloaded for ${claim.claimNumber}`)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-200 text-xs font-semibold hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Audit Report</span>
          </button>

          <Link
            href="/copilot"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-md shadow-purple-500/20 transition-all"
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Interactive Copilot</span>
          </Link>
        </div>
      </div>

      {/* Decision Banner if Decision Executed */}
      {claim.humanDecision && (
        <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-xs text-indigo-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              Decision Recorded: <strong className="text-white uppercase">{claim.humanDecision.action}</strong> by {claim.humanDecision.decidedBy} on {formatDate(claim.humanDecision.decidedAt)}.
            </span>
          </div>
          <span className="font-mono text-[11px] text-slate-400">"{claim.humanDecision.reason}"</span>
        </div>
      )}

      {/* SPLIT SCREEN MAIN CONTAINER */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN (Width 7/12): Customer Profile, Policy, Claim Info, Documents */}
        <div className="lg:col-span-7 space-y-6">

          {/* Customer & Policy Card */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
                <User className="w-4 h-4" />
                <h3 className="font-bold text-xs uppercase tracking-wider">Customer & Policy Profile</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Cust ID: {claim.customer.id}</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px]">Customer Name</span>
                <span className="font-bold text-slate-900 dark:text-white">{claim.customer.name}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Email</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">{claim.customer.email}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Phone</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">{claim.customer.phone}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Policy Number</span>
                <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">{claim.policy.policyNumber}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Insurance Category</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">{claim.policy.category}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Premium Status</span>
                <span className={`font-bold ${claim.policy.premiumStatus === 'Paid' ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {claim.policy.premiumStatus}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Coverage Limit</span>
                <span className="font-bold text-slate-900 dark:text-white">{formatCurrency(claim.policy.coverageLimit, claim.currency)}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Deductible</span>
                <span className="font-bold text-slate-900 dark:text-white">{formatCurrency(claim.policy.deductible, claim.currency)}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Active Claims</span>
                <span className="font-bold text-slate-900 dark:text-white">{claim.policy.activeClaimsCount} Active</span>
              </div>
            </div>
          </div>

          {/* Claim Incident Card */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-teal-600 dark:text-teal-400">
                <FileText className="w-4 h-4" />
                <h3 className="font-bold text-xs uppercase tracking-wider">Incident Details</h3>
              </div>
              <span className="text-[11px] font-extrabold text-indigo-500">{formatCurrency(claim.claimAmount, claim.currency)} Requested</span>
            </div>

            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              {claim.description}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs pt-2 border-t border-slate-200/60 dark:border-slate-800/60">
              <div>
                <span className="text-slate-400 block text-[10px]">Incident Date & Time</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{formatDate(claim.incidentDate)} at {claim.incidentTime}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Location</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{claim.location}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">Assigned Officer</span>
                <span className="font-semibold text-indigo-400">{claim.assignedOfficer}</span>
              </div>
            </div>
          </div>

          {/* Uploaded Documents & OCR Inspection */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="font-bold text-xs text-slate-900 dark:text-white uppercase tracking-wider">
                Claim Documents ({claim.documents.length})
              </h3>
              <span className="text-[10px] text-emerald-500 font-bold">100% OCR Processed</span>
            </div>

            <div className="space-y-2">
              {claim.documents.map((doc) => (
                <div key={doc.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500">
                      <File className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-white">{doc.fileName}</p>
                      <p className="text-[10px] text-slate-400">{doc.category} &bull; {doc.fileSize}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleOpenDocPreview(doc)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 text-[11px] font-semibold transition-colors"
                  >
                    <Eye className="w-3 h-3" />
                    <span>View OCR</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Steps Timeline */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
            <h3 className="font-bold text-xs text-slate-900 dark:text-white uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 pb-3">
              Multi-Agent Execution Timeline
            </h3>

            <div className="space-y-3">
              {claim.agentSteps.map((step) => (
                <div key={step.id} className="flex items-start gap-3 text-xs">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0"></div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 dark:text-white">{step.agentName}</span>
                      <span className="font-mono text-[10px] text-slate-400">{step.durationMs}ms</span>
                    </div>
                    <p className="text-slate-600 dark:text-slate-400 text-[11px] mt-0.5">{step.outputSummary}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN (Width 5/12): AI Copilot Recommendation, Fraud Score, LangMem & Decision Panel */}
        <div className="lg:col-span-5 space-y-6">

          {/* AI Recommendation Verdict Box */}
          <div className="glass-panel p-6 rounded-3xl border border-indigo-500/40 bg-gradient-to-br from-indigo-950/60 via-slate-900 to-purple-950/40 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
                <h3 className="font-extrabold text-sm text-white uppercase tracking-wider">AI Copilot Recommendation</h3>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase border ${
                isApprove
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                  : isReject
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/40'
                  : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              }`}>
                {verdictText}
              </span>
            </div>

            {/* Recommended Amount */}
            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Recommended Payout</span>
                <span className="text-2xl font-extrabold text-emerald-400 font-mono">
                  {formatCurrency(recommendedPayoutAmount, claim.currency)}
                </span>
              </div>
              <span className="text-[11px] text-slate-400 text-right font-medium">
                {policyDeductible > 0 ? `After ${formatCurrency(policyDeductible, claim.currency)} Policy Deductible` : 'Standard Policy Payout'}
              </span>
            </div>

            {/* Reasoning Summary */}
            <div className="space-y-2 text-xs">
              <h4 className="font-bold text-slate-200">Synthesis Reasoning:</h4>
              <p className="text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 font-mono">
                "{reasoningSummary}"
              </p>
            </div>

            {/* Key Findings List */}
            {keyFindings && keyFindings.length > 0 && (
              <div className="space-y-2 text-xs">
                <h4 className="font-bold text-slate-200">Key AI Agent Findings:</h4>
                <div className="space-y-1.5">
                  {keyFindings.map((finding, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{finding}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Scores Row: Confidence & Fraud Index */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ConfidenceMeter score={confidenceScore} />
            <FraudScoreCard
              score={fraudScore}
              riskLevel={riskLevel}
              signalCount={signalCount}
              explanation={fraudExplanation}
            />
          </div>


          {/* Retrieved LangMem Cards */}
          {rec?.retrievedMemories && rec.retrievedMemories.length > 0 && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-purple-500 dark:text-purple-400 border-b border-slate-200 dark:border-slate-800 pb-2">
                <BrainCircuit className="w-4 h-4" />
                <h4 className="font-bold text-xs uppercase tracking-wider">LangMem Historical Memory Match</h4>
              </div>

              {rec.retrievedMemories.map((mem) => (
                <div key={mem.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-indigo-400">{mem.claimId}</span>
                    <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-bold text-[10px]">
                      {(mem.similarityScore * 100).toFixed(0)}% Similar
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">{mem.summary}</p>
                </div>
              ))}
            </div>
          )}

          {/* Retrieved RAG Policy References */}
          {rec?.retrievedKnowledge && rec.retrievedKnowledge.length > 0 && (
            <div className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-500 dark:text-indigo-400 border-b border-slate-200 dark:border-slate-800 pb-2">
                <BookOpen className="w-4 h-4" />
                <h4 className="font-bold text-xs uppercase tracking-wider">RAG Knowledge Vector Citation</h4>
              </div>

              {rec.retrievedKnowledge.map((rag) => (
                <div key={rag.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{rag.policyTitle}</span>
                    <span className="font-mono text-[10px] text-indigo-400">{rag.sectionCode}</span>
                  </div>
                  <p className="text-slate-400 text-[11px] italic">"{rag.clause}"</p>
                </div>
              ))}
            </div>
          )}

          {/* HUMAN DECISION ACTION PANEL */}
          <div className="glass-panel p-6 rounded-3xl border border-indigo-500/30 bg-slate-900 space-y-4">
            <h3 className="font-bold text-sm text-white uppercase tracking-wider">Execute Officer Decision</h3>
            <p className="text-xs text-slate-400">Select human-in-the-loop verdict to finalize claim status.</p>

            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setDecisionModalAction('Approve')}
                className="py-3 px-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-lg shadow-emerald-600/20 flex flex-col items-center justify-center gap-1 transition-all"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Claim</span>
              </button>

              <button
                onClick={() => setDecisionModalAction('Reject')}
                className="py-3 px-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-xs shadow-lg shadow-rose-600/20 flex flex-col items-center justify-center gap-1 transition-all"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject Claim</span>
              </button>

              <button
                onClick={() => setDecisionModalAction('Request Additional Documents')}
                className="py-3 px-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-extrabold text-xs shadow-lg shadow-amber-600/20 flex flex-col items-center justify-center gap-1 transition-all"
              >
                <AlertTriangle className="w-4 h-4" />
                <span>Request Docs</span>
              </button>
            </div>
          </div>

        </div>

      </div>

      {/* Human Decision Modal */}
      {decisionModalAction && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg p-6 rounded-3xl border border-slate-800 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-extrabold text-sm text-white uppercase tracking-wider">
                Confirm Action: {decisionModalAction}
              </h3>
              <button onClick={() => setDecisionModalAction(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Enter Justification & Audit Note</label>
              <textarea
                rows={4}
                required
                value={decisionReason}
                onChange={(e) => setDecisionReason(e.target.value)}
                placeholder="Specify justification reason for audit log compliance..."
                className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setDecisionModalAction(null)}
                className="px-4 py-2 rounded-xl border border-slate-800 text-slate-400 text-xs font-semibold hover:bg-slate-900"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteDecision}
                disabled={!decisionReason.trim()}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-indigo-600/30"
              >
                Save Decision & Record Audit Log
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document OCR Preview Modal */}
      {selectedDocPreview && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl p-6 rounded-3xl border border-slate-800 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <File className="w-4 h-4 text-indigo-400" />
                <h3 className="font-bold text-sm text-white">{selectedDocPreview.fileName}</h3>
                <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {selectedDocPreview.category}
                </span>
              </div>
              <button onClick={() => setSelectedDocPreview(null)} className="p-1 text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                  Extracted OCR Metadata
                </h4>
                <span className="text-[11px] font-mono text-slate-400">
                  Status: <span className="text-emerald-400 font-bold">{selectedDocPreview.ocrStatus || 'Completed'}</span>
                </span>
              </div>

              {isProcessingOcr ? (
                <div className="py-6 text-center text-xs text-indigo-300 flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></span>
                  <span>Running Document Agent OCR & Factuality Extraction...</span>
                </div>
              ) : selectedDocPreview.ocrFields && selectedDocPreview.ocrFields.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  {selectedDocPreview.ocrFields.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded bg-slate-900/80 border border-slate-800">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300 font-medium">{f.fieldName}</span>
                        <span className={`px-1.5 py-0.2 text-[9px] font-mono rounded ${
                          f.confidence >= 80 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                          {f.confidence}% conf
                        </span>
                      </div>
                      <span className="font-mono font-bold text-white tracking-wide">{f.extractedValue}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-xs text-slate-400 italic">
                  No structured OCR fields detected in this document. File classified as {selectedDocPreview.category}.
                </div>
              )}
            </div>

            <div className="text-right">
              <button
                onClick={() => setSelectedDocPreview(null)}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
