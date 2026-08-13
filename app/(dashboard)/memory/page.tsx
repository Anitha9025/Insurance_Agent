'use client';

import React, { useState } from 'react';
import { 
  BrainCircuit, 
  Search, 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ArrowUpRight, 
  Tag, 
  Layers,
  Network,
  Share2
} from 'lucide-react';
import { mockLangMemNodes } from '@/lib/data/mockData';
import { formatCurrency } from '@/lib/utils';

export default function MemoryPage() {
  const [selectedNode, setSelectedNode] = useState(mockLangMemNodes[0]);
  const [searchFilter, setSearchFilter] = useState('');

  const filteredMemories = mockLangMemNodes.filter((m) =>
    m.summary.toLowerCase().includes(searchFilter.toLowerCase()) ||
    m.claimId.toLowerCase().includes(searchFilter.toLowerCase()) ||
    m.tags.some(t => t.toLowerCase().includes(searchFilter.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 text-[11px] font-bold uppercase tracking-wider">
              LangMem Vector Memory Graph
            </span>
            <span className="text-xs text-slate-400">14,290 Stored Claims Nodes</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            LangMem Agentic Memory Inspector
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Inspect historical resolution patterns, vector similarity clusters, and cross-claim subrogation learning.
          </p>
        </div>
      </div>

      {/* Main Grid: Graph Visualizer + Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column (Width 7/12): Memory Graph Visualization & List */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* Visual Memory Graph Cluster Mock */}
          <div className="glass-panel p-6 rounded-3xl border border-purple-500/30 bg-gradient-to-br from-slate-950 via-indigo-950/40 to-purple-950/40 space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-purple-400 font-bold text-xs">
                <Network className="w-4 h-4 animate-pulse" />
                <span>Vector Cluster Graph (Cosine Similarity Threshold &gt; 0.80)</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">Active Query: Auto Highway Subrogation</span>
            </div>

            {/* Interactive Graph Node Display */}
            <div className="h-56 w-full rounded-2xl bg-slate-950/80 border border-slate-800 p-4 relative flex items-center justify-center overflow-hidden">
              {/* Connecting Lines SVG */}
              <svg className="absolute inset-0 w-full h-full stroke-purple-500/30 stroke-2 pointer-events-none">
                <line x1="20%" y1="30%" x2="50%" y2="50%" />
                <line x1="80%" y1="25%" x2="50%" y2="50%" />
                <line x1="30%" y1="75%" x2="50%" y2="50%" />
                <line x1="75%" y1="80%" x2="50%" y2="50%" />
              </svg>

              {/* Central Active Node */}
              <div className="z-10 w-20 h-20 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 border-2 border-purple-300 shadow-xl shadow-purple-500/30 flex flex-col items-center justify-center text-white text-center p-1">
                <BrainCircuit className="w-5 h-5 animate-pulse" />
                <span className="text-[9px] font-bold mt-1">CLM-8841</span>
              </div>

              {/* Surrounding Connected Memory Nodes */}
              <button
                onClick={() => setSelectedNode(mockLangMemNodes[0])}
                className="absolute top-6 left-10 p-3 rounded-2xl bg-slate-900 border border-emerald-500/40 hover:border-emerald-400 text-left space-y-0.5 shadow-lg group transition-all"
              >
                <div className="flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-400">
                  <span>CLM-2025-4109</span>
                  <span>(94%)</span>
                </div>
                <span className="text-[9px] text-slate-400 block">I-95 Subrogation</span>
              </button>

              <button
                onClick={() => setSelectedNode(mockLangMemNodes[1])}
                className="absolute top-4 right-10 p-3 rounded-2xl bg-slate-900 border border-indigo-500/40 hover:border-indigo-400 text-left space-y-0.5 shadow-lg group transition-all"
              >
                <div className="flex items-center gap-1 text-[10px] font-mono font-bold text-indigo-400">
                  <span>CLM-2024-9120</span>
                  <span>(89%)</span>
                </div>
                <span className="text-[9px] text-slate-400 block">Apex Auto Repair</span>
              </button>

              <button
                onClick={() => setSelectedNode(mockLangMemNodes[2])}
                className="absolute bottom-6 left-16 p-3 rounded-2xl bg-slate-900 border border-rose-500/40 hover:border-rose-400 text-left space-y-0.5 shadow-lg group transition-all"
              >
                <div className="flex items-center gap-1 text-[10px] font-mono font-bold text-rose-400">
                  <span>CLM-2025-1092</span>
                  <span>(86%)</span>
                </div>
                <span className="text-[9px] text-slate-400 block">Suspicious Arson</span>
              </button>
            </div>
          </div>

          {/* Search Memory Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search vector memory nodes by claim ID, tag, or outcome..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:outline-none"
            />
          </div>

          {/* Memory List */}
          <div className="space-y-3">
            {filteredMemories.map((mem) => (
              <div
                key={mem.id}
                onClick={() => setSelectedNode(mem)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  selectedNode.id === mem.id
                    ? 'bg-purple-950/40 border-purple-500/50 shadow-md'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-indigo-400">{mem.claimId}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                      mem.resolutionOutcome === 'Approved' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                    }`}>
                      {mem.resolutionOutcome} ({formatCurrency(mem.resolvedAmount)})
                    </span>
                  </div>
                  <span className="font-mono font-bold text-purple-400 text-xs">{(mem.similarityScore * 100).toFixed(0)}% Match</span>
                </div>

                <p className="text-xs text-slate-300 mt-2 leading-relaxed">{mem.summary}</p>

                <div className="flex items-center gap-1.5 mt-3 pt-2 border-t border-slate-800">
                  {mem.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                      #{t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* Right Column (Width 5/12): Selected Memory Node Deep Dive */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel p-6 rounded-3xl border border-purple-500/30 bg-slate-900 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-purple-400">
                <BrainCircuit className="w-5 h-5" />
                <h3 className="font-bold text-sm text-white">Memory Node Deep Dive</h3>
              </div>
              <span className="font-mono font-bold text-indigo-400 text-xs">{selectedNode.claimId}</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Similarity Reason</span>
                <p className="text-slate-200 mt-0.5 font-medium">{selectedNode.relevanceReason}</p>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Resolution Outcome</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-extrabold ${
                    selectedNode.resolutionOutcome === 'Approved' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {selectedNode.resolutionOutcome}
                  </span>
                  <span className="font-mono font-bold text-white text-sm">
                    {formatCurrency(selectedNode.resolvedAmount)}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Full Case Executive Summary</span>
                <p className="text-slate-300 mt-1 leading-relaxed bg-slate-950 p-3 rounded-xl border border-slate-800">
                  {selectedNode.summary}
                </p>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Associated Vector Tags</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {selectedNode.tags.map((t) => (
                    <span key={t} className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 text-[11px] font-semibold border border-indigo-500/20">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
