'use client';

import React, { useState } from 'react';
import { 
  Settings, 
  User, 
  Sun, 
  Moon, 
  Bell, 
  Cpu, 
  BookOpen, 
  BrainCircuit, 
  Key, 
  Save, 
  CheckCircle2,
  Sliders,
  ShieldCheck
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';

export default function SettingsPage() {
  const { theme, toggleTheme } = useClaims();
  const [activeTab, setActiveTab] = useState<'profile' | 'llm' | 'rag' | 'memory' | 'keys'>('llm');

  // Form states
  const [selectedModel, setSelectedModel] = useState('gpt-4o');
  const [temperature, setTemperature] = useState('0.2');
  const [ragTopK, setRagTopK] = useState('5');
  const [ragSimilarity, setRagSimilarity] = useState('0.82');
  const [memoryRetention, setMemoryRetention] = useState('365');
  const [apiKey, setApiKey] = useState('sk-proj-nexus-claims-••••••••••••••••');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold uppercase tracking-wider">
              System Administration
            </span>
            <span className="text-xs text-slate-400">Portal Version 3.4</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mt-1">
            Enterprise Copilot Configuration
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Configure LLM parameters, RAG vector retrieval top-K, LangMem retention decay, and API hardware keys.
          </p>
        </div>

        {savedSuccess && (
          <div className="px-3.5 py-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-bold flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4" />
            <span>Settings Saved Successfully!</span>
          </div>
        )}
      </div>

      {/* Settings Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 text-xs overflow-x-auto">
        {[
          { id: 'llm', label: 'LLM Swarm Config', icon: Cpu },
          { id: 'rag', label: 'RAG Vector Index', icon: BookOpen },
          { id: 'memory', label: 'LangMem Memory', icon: BrainCircuit },
          { id: 'profile', label: 'Officer Profile', icon: User },
          { id: 'keys', label: 'API Keys & Secrets', icon: Key },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-bold transition-all whitespace-nowrap ${
                isActive
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Settings Content Area */}
      <form onSubmit={handleSaveSettings} className="space-y-6">
        
        {/* Tab 1: LLM Config */}
        {activeTab === 'llm' && (
          <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Large Language Model Swarm Settings</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1.5">Primary Reasoning Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-semibold focus:ring-2 focus:ring-purple-500 focus:outline-none"
                >
                  <option value="gpt-4o">OpenAI GPT-4o (Default Swarm Lead)</option>
                  <option value="claude-3.5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                  <option value="gemini-1.5-pro">Google Gemini 1.5 Pro (1M Context)</option>
                </select>
                <p className="text-[11px] text-slate-400 mt-1">Used for final recommendation synthesis & rationale generation.</p>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1.5">Sampling Temperature ({temperature})</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(e.target.value)}
                  className="w-full accent-purple-500 mt-2"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>0.0 (Deterministic / Strict)</span>
                  <span>1.0 (Creative)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: RAG Config */}
        {activeTab === 'rag' && (
          <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-6">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-400" />
              <span>RAG Vector Search Parameters</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Top-K Retrieved Context Clauses</label>
                <input
                  type="number"
                  value={ragTopK}
                  onChange={(e) => setRagTopK(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-bold"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Cosine Similarity Cutoff Threshold ({ragSimilarity})</label>
                <input
                  type="number"
                  step="0.01"
                  value={ragSimilarity}
                  onChange={(e) => setRagSimilarity(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-bold"
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: LangMem Config */}
        {activeTab === 'memory' && (
          <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-6">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-purple-400" />
              <span>LangMem Vector Memory Store</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Memory Vector Retention Window (Days)</label>
                <input
                  type="number"
                  value={memoryRetention}
                  onChange={(e) => setMemoryRetention(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white font-bold"
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Officer Profile & Theme */}
        {activeTab === 'profile' && (
          <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-6">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4 text-indigo-400" />
              <span>Officer Profile & UI Theme</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Interface Color Mode</label>
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-white font-bold"
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
                  <span>Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: API Keys */}
        {activeTab === 'keys' && (
          <div className="glass-panel p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-6">
            <h3 className="font-bold text-sm text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <Key className="w-4 h-4 text-amber-400" />
              <span>API Keys & Encryption Vault</span>
            </h3>

            <div>
              <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1 text-xs">OpenAI Secret API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white font-mono"
              />
            </div>
          </div>
        )}

        {/* Submit Save Button */}
        <div className="pt-2 text-right">
          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-extrabold text-xs shadow-lg shadow-indigo-600/30 transition-all ml-auto"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>
        </div>

      </form>
    </div>
  );
}
