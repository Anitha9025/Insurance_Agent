'use client';

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Sparkles, 
  FileText, 
  Upload, 
  CheckCircle2, 
  AlertTriangle, 
  Trash2, 
  RefreshCw,
  Zap,
  Bookmark
} from 'lucide-react';
import { 
  uploadKnowledgeDocument, 
  fetchKnowledgeDocuments, 
  queryKnowledgeBase, 
  deleteKnowledgeDocument 
} from '@/lib/api';

export default function KnowledgeBasePage() {
  const [searchQuery, setSearchQuery] = useState('collision policy coverage deductible clauses');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [documents, setDocuments] = useState<any[]>([]);
  const [ragResult, setRagResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docTitle, setDocTitle] = useState('');
  const [rawText, setRawText] = useState('');
  const [activeTab, setActiveTab] = useState<'search' | 'upload'>('search');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await fetchKnowledgeDocuments();
      setDocuments(docs || []);
    } catch (err) {
      console.error('Failed to load knowledge documents:', err);
    }
  };

  const handleVectorSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await queryKnowledgeBase(searchQuery, selectedCategory === 'All' ? undefined : selectedCategory);
      setRagResult(res);
    } catch (err) {
      console.error('RAG query failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile && !rawText) return;
    setUploading(true);

    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append('file', selectedFile);
      } else {
        const blob = new Blob([rawText], { type: 'text/plain' });
        formData.append('file', blob, 'manual_policy_text.txt');
      }
      if (docTitle) formData.append('title', docTitle);
      formData.append('document_type', selectedCategory === 'All' ? 'policy' : selectedCategory.toLowerCase());

      await uploadKnowledgeDocument(formData);
      setSelectedFile(null);
      setDocTitle('');
      setRawText('');
      await loadDocuments();
      setActiveTab('search');
    } catch (err) {
      console.error('Document upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id: string) => {
    try {
      await deleteKnowledgeDocument(id);
      await loadDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 text-[11px] font-bold uppercase tracking-wider">
              RAG Vector Store (PostgreSQL Vector Engine)
            </span>
            <span className="text-xs text-slate-400">Cloud Embedding API: Gemini text-embedding-004</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Policy Knowledge Base & RAG Engine
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Dynamically ingest policy documents, retrieve grounded policy clauses, and present vector citations for AI agents.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'search'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
            }`}
          >
            RAG Query
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'upload'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
            }`}
          >
            + Ingest Document
          </button>
        </div>
      </div>

      {activeTab === 'search' ? (
        <>
          {/* Vector Search Container */}
          <div className="glass-panel p-6 rounded-3xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900 to-purple-950/40 space-y-4">
            <div className="relative">
              <Search className="w-5 h-5 text-indigo-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleVectorSearch()}
                placeholder="Perform grounded semantic vector query across uploaded policy manuals..."
                className="w-full pl-12 pr-32 py-3.5 rounded-2xl bg-slate-950/90 border border-indigo-500/40 text-xs text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:outline-none shadow-lg"
              />
              <button
                onClick={handleVectorSearch}
                disabled={loading}
                className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-purple-500/20 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Vector Search</span>
              </button>
            </div>

            <div className="flex items-center gap-2 text-xs overflow-x-auto">
              <span className="text-slate-400 font-medium">Policy Sector:</span>
              {['All', 'Vehicle', 'Health', 'Home', 'Travel'].map((cat) => (
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

          {/* RAG Search Results */}
          {ragResult && (
            <div className="glass-panel p-6 rounded-3xl border border-purple-500/30 bg-slate-900/60 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-white">Grounded RAG Reasoning Output</h3>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className={`px-2.5 py-0.5 rounded-full font-bold ${
                    ragResult.is_grounded ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}>
                    Grounding Confidence: {ragResult.confidence}%
                  </span>
                  {ragResult.uncertainty_flag && (
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[11px] flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Low Confidence Flag
                    </span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                {ragResult.answer}
              </div>

              {/* Citations List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cited Policy Chunks ({ragResult.citations?.length || 0})</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {ragResult.citations?.map((c: any, i: number) => (
                    <div key={i} className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-semibold text-purple-300">
                        <span>{c.document_title}</span>
                        <span className="text-[10px] text-slate-400">Similarity: {Math.round(c.similarity_score * 100)}%</span>
                      </div>
                      <p className="text-[11px] text-slate-400 italic leading-snug">"{c.snippet}"</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Active Knowledge Documents List */}
          {(() => {
            const filteredDocs = selectedCategory === 'All'
              ? documents
              : documents.filter((doc) => {
                  const typeStr = (doc.document_type || '').toLowerCase();
                  const titleStr = (doc.title || '').toLowerCase();
                  const catStr = selectedCategory.toLowerCase();
                  return typeStr === catStr || titleStr.includes(catStr) || (doc.policy_number && doc.policy_number.toLowerCase().includes(catStr));
                });

            return (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Active Ingested Documents ({filteredDocs.length}{selectedCategory !== 'All' ? ` filtered for ${selectedCategory}` : ''})
                  </h3>
                  {selectedCategory !== 'All' && (
                    <span className="text-[11px] text-purple-400 font-medium">
                      Showing {filteredDocs.length} of {documents.length} total documents
                    </span>
                  )}
                </div>

                {filteredDocs.length === 0 ? (
                  <div className="p-8 text-center rounded-2xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400">
                    No policy documents found matching sector "{selectedCategory}". Click "+ Ingest Document" to add active policy manuals.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredDocs.map((doc) => (
                      <div key={doc.id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-purple-400" />
                            <h4 className="text-xs font-bold text-white">{doc.title}</h4>
                          </div>
                          <div className="flex items-center gap-3 text-[11px] text-slate-400">
                            <span>Type: {doc.document_type}</span>
                            <span>Chunks: {doc.chunks_count}</span>
                            {doc.policy_number && <span className="font-mono text-purple-300 font-medium">Policy: {doc.policy_number}</span>}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteDoc(doc.id)}
                          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-all"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })()}

        </>
      ) : (
        /* Document Ingestion Form */
        <form onSubmit={handleFileUpload} className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 max-w-2xl">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Upload className="w-4 h-4 text-purple-400" />
            Ingest Policy Knowledge Manual / Text
          </h2>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Document Title</label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="e.g. Master Vehicle Comprehensive Coverage Guidelines 2026"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Upload Text/Policy File</label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Or Paste Policy Text Directly</label>
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste raw insurance policy clauses, exclusions, deductibles, or guidelines here..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={uploading || (!selectedFile && !rawText)}
            className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-500/20 disabled:opacity-50"
          >
            {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>{uploading ? 'Processing & Embedding Chunks...' : 'Embed & Save Knowledge'}</span>
          </button>
        </form>
      )}
    </div>
  );
}
