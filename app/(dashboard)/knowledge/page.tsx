'use client';

import React, { useState } from 'react';
import { 
  BookOpen, 
  Search, 
  Filter, 
  Sparkles, 
  FileText, 
  ExternalLink, 
  CheckCircle2,
  ChevronRight,
  Zap,
  Bookmark
} from 'lucide-react';
import { mockRAGDocuments } from '@/lib/data/mockData';

export default function KnowledgeBasePage() {
  const [searchQuery, setSearchQuery] = useState('collision police report deductible subrogation');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const filteredKnowledge = mockRAGDocuments.filter((doc) =>
    doc.policyTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.clause.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.sectionCode.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 text-[11px] font-bold uppercase tracking-wider">
              RAG Vector Index (Dense Retrieval)
            </span>
            <span className="text-xs text-slate-400">pgvector + HNSW Index</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Policy Knowledge Base & RAG Engine
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Query master insurance policies, statutory subrogation guidelines, emergency medical coverage rules, and endorsement riders.
          </p>
        </div>
      </div>

      {/* Vector Search Bar Container */}
      <div className="glass-panel p-6 rounded-3xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-purple-950/40 space-y-4">
        <div className="relative">
          <Search className="w-5 h-5 text-indigo-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Perform semantic vector query across insurance policy manuals..."
            className="w-full pl-12 pr-28 py-3.5 rounded-2xl bg-slate-950/90 border border-indigo-500/40 text-xs text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:outline-none shadow-lg"
          />
          <button
            onClick={() => setSearchQuery(searchQuery)}
            className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-purple-500/20"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Vector Search</span>
          </button>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 text-xs overflow-x-auto">
          <span className="text-slate-400 font-medium">Policy Sector:</span>
          {['All', 'Auto Collision', 'Health Emergency', 'Home & Solar', 'Subrogation Law'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-xl text-[11px] font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs font-bold text-slate-400">
          <span>Vector Matches Found ({filteredKnowledge.length})</span>
          <span className="font-mono text-purple-400">Embeddings Model: text-embedding-3-large</span>
        </div>

        <div className="space-y-4">
          {filteredKnowledge.map((rag) => (
            <div
              key={rag.id}
              className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3 hover:border-purple-500/40 transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-indigo-400">{rag.sectionCode}</span>
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-extrabold text-[10px] border border-emerald-500/20">
                      {(rag.matchScore * 100).toFixed(0)}% Vector Match
                    </span>
                  </div>
                  <h3 className="font-bold text-base text-slate-900 dark:text-white mt-1">{rag.policyTitle}</h3>
                </div>

                <button
                  onClick={() => alert(`Viewing full document for ${rag.sectionCode}`)}
                  className="p-2 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-400 hover:text-white transition-colors"
                  title="Inspect Full Section PDF"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>

              {/* Clause Highlight Box */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs leading-relaxed text-slate-800 dark:text-slate-200">
                <span className="font-semibold text-purple-400 block mb-1">Exact Policy Clause:</span>
                "{rag.clause}"
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-200/60 dark:border-slate-800/60">
                <span className="italic">{rag.excerpt}</span>
                <span className="font-semibold text-indigo-400">Cited in 14 recent claims &rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
