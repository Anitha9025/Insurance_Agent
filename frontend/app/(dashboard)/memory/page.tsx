'use client';

import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Search,
  Sparkles,
  Layers,
  Loader2,
  Database,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { fetchMemories } from '@/lib/api';

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState('vehicle collision approval deductible');
  const [isLoading, setIsLoading] = useState(false);
  const [memories, setMemories] = useState<any[]>([]);

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      const res = await fetchMemories(searchQuery);
      setMemories(res.memories || []);
    } catch (err) {
      console.error('Error searching memory:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-bold uppercase tracking-wider">
              Agentic Claim Memory Store (Phase 6)
            </span>
            <span className="text-xs text-slate-400">Semantic Vector Store (PostgreSQL)</span>
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight mt-1">
            Claim History & Decision Memory Engine
          </h1>
          <p className="text-xs text-slate-400">
            Search stored historical claim decisions, validated OCR insights, and officer rationale using vector cosine similarity.
          </p>
        </div>
      </div>

      {/* Search Input Bar */}
      <div className="glass-panel p-4 rounded-2xl bg-slate-900/60 border border-indigo-500/30 space-y-3">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-indigo-400" />
            <input
              type="text"
              placeholder="Search memory vector database by query, category, or claim decision..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors shadow-md shadow-purple-500/20 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Vector Search</span>
          </button>
        </div>

        {/* Sample Query Presets */}
        <div className="flex flex-wrap items-center gap-2 text-xs pt-1 border-t border-slate-800/60">
          <span className="text-slate-400 text-[11px] font-semibold">Quick Searches:</span>
          {['vehicle collision deductible', 'approved payout rationale', 'police report verification', 'fraud risk analysis'].map((q) => (
            <button
              key={q}
              onClick={() => {
                setSearchQuery(q);
                fetchMemories(q).then((res) => setMemories(res.memories || []));
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-purple-950/60 text-slate-300 hover:text-purple-200 border border-slate-700/60 hover:border-purple-500/40 text-[11px] transition-all"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Memories Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs text-slate-400 font-bold">
          <span>Historical Memories Matches ({memories.length})</span>
          <span className="font-mono text-purple-400">Embedding Dim: 768 Float Vector</span>
        </div>

        {memories.length === 0 ? (
          <div className="glass-panel p-10 rounded-3xl border border-slate-800 text-center space-y-3">
            <Database className="w-8 h-8 text-purple-400 mx-auto opacity-60" />
            <h3 className="text-sm font-bold text-white">No Matching Claim Memories Found</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Memories are automatically recorded when claims complete multi-agent evaluation or when officers record decisions.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {memories.map((mem: any) => (
              <div key={mem.memory_id} className="glass-panel p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <BrainCircuit className="w-4 h-4 text-purple-400" />
                    <span className="font-mono text-xs font-bold text-white">Claim #{mem.claim_number || mem.claim_id}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 text-[10px] font-mono font-bold">
                    Similarity: {Math.round((mem.similarity_score || 1.0) * 100)}%
                  </span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center gap-2 text-slate-400">
                    <span className="font-bold text-purple-300">Type:</span> {mem.memory_type} ({mem.memory_key})
                  </div>
                  <p className="text-slate-300 leading-relaxed bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 font-mono text-[11px]">
                    "{mem.memory_value}"
                  </p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <span>Source Agent: {mem.source_agent || 'System'}</span>
                  <span>Confidence: {Math.round((mem.confidence_score || 1.0) * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
