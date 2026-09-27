'use client';

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Filter, 
  Terminal, 
  BrainCircuit, 
  BookOpen, 
  User, 
  Bot, 
  CheckCircle2, 
  Download,
  Calendar,
  Trash2
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';
import { formatDate } from '@/lib/utils';

export default function AuditLogsPage() {
  const { auditLogs, clearAuditLogs, removeAuditLog } = useClaims();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedActor, setSelectedActor] = useState<string>('ALL');
  const [isClearingAll, setIsClearingAll] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all audit log entries from the database? This action cannot be undone.')) {
      return;
    }
    setIsClearingAll(true);
    try {
      await clearAuditLogs();
    } catch (err) {
      alert(`Failed to clear audit logs: ${(err as Error).message}`);
    } finally {
      setIsClearingAll(false);
    }
  };

  const handleDeleteSingle = async (logId: string) => {
    setDeletingId(logId);
    try {
      await removeAuditLog(logId);
    } catch (err) {
      alert(`Failed to delete log entry: ${(err as Error).message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const filteredLogs = auditLogs.filter((log) => {
    const matchesSearch =
      (log.claimNumber || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.action || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.actorName || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.details || '').toLowerCase().includes(searchQuery.toLowerCase());

    const matchesActor = selectedActor === 'ALL' || log.actorType === selectedActor;

    return matchesSearch && matchesActor;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[11px] font-bold uppercase tracking-wider">
              Immutable Trace Log
            </span>
            <span className="text-xs text-slate-400">SOC2 Type II Compliant</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Multi-Agent & Officer Audit Trail
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Complete chronological record of all agent execution steps, vector memory lookups, tool parameters, and human decision overwrites.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {auditLogs.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={isClearingAll}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold transition-all disabled:opacity-50"
              title="Clear all audit log records from database"
            >
              <Trash2 className="w-4 h-4" />
              <span>{isClearingAll ? 'Clearing Logs...' : `Clear Audit Logs (${auditLogs.length})`}</span>
            </button>
          )}

          <button
            onClick={() => alert('Exporting compliance audit log package...')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs shadow-md transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Export Compliance Log (JSON)</span>
          </button>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search audit log by claim ID, agent name, tool, or action..."
            className="w-full pl-10 pr-4 py-2 text-xs rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Actor Type:</span>
          {['ALL', 'Officer', 'AI Agent'].map((actor) => (
            <button
              key={actor}
              onClick={() => setSelectedActor(actor)}
              className={`px-3 py-1.5 rounded-xl font-semibold text-[11px] transition-all ${
                selectedActor === actor
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800'
              }`}
            >
              {actor}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Timeline Feed */}
      <div className="space-y-3">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log) => (
            <div key={log.id} className="glass-panel p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
              <div className="flex items-start justify-between border-b border-slate-200/60 dark:border-slate-800/60 pb-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs ${
                      log.actorType === 'Officer'
                        ? 'bg-indigo-500/10 text-indigo-500 border border-indigo-500/20'
                        : 'bg-purple-500/10 text-purple-500 border border-purple-500/20'
                    }`}
                  >
                    {log.actorType === 'Officer' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 dark:text-white">{log.action}</span>
                      <span className="font-mono font-bold text-indigo-400 text-xs">{log.claimNumber}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                      <span>Actor: <strong className="text-slate-300">{log.actorName}</strong></span>
                      <span>&bull;</span>
                      <span>{formatDate(log.timestamp)} at {new Date(log.timestamp).toLocaleTimeString()}</span>
                      {log.ipAddress && (
                        <>
                          <span>&bull;</span>
                          <span className="font-mono text-slate-500">IP: {log.ipAddress}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-[10px] font-bold text-slate-400">
                    {log.actorType}
                  </span>
                  <button
                    onClick={() => handleDeleteSingle(log.id)}
                    disabled={deletingId === log.id}
                    className="p-1 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition-colors disabled:opacity-50"
                    title="Delete log entry"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-mono bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200/60 dark:border-slate-800">
                {log.details}
              </p>

              {/* Traces & Vectors Meta Row */}
              <div className="flex flex-wrap items-center gap-3 text-[10px] pt-1 text-slate-400">
                {log.memoryUsed && (
                  <div className="flex items-center gap-1 text-purple-400">
                    <BrainCircuit className="w-3 h-3" />
                    <span>Memory: {log.memoryUsed}</span>
                  </div>
                )}
                {log.knowledgeUsed && (
                  <div className="flex items-center gap-1 text-indigo-400">
                    <BookOpen className="w-3 h-3" />
                    <span>RAG: {log.knowledgeUsed}</span>
                  </div>
                )}
                {log.toolsCalled && log.toolsCalled.length > 0 && (
                  <div className="flex items-center gap-1 text-teal-400 font-mono">
                    <Terminal className="w-3 h-3" />
                    <span>Tools: [{log.toolsCalled.join(', ')}]</span>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="p-12 text-center border-2 border-dashed border-slate-800 rounded-3xl text-xs text-slate-500 space-y-1">
            <div className="font-semibold text-slate-400">No Audit Logs Found</div>
            <div>No matching activity records returned from PostgreSQL audit trail.</div>
          </div>
        )}
      </div>
    </div>
  );
}

