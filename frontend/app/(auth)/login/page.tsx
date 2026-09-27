'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Sparkles, ArrowRight, Lock, Mail, ShieldCheck, CheckCircle2, Zap } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('s.jenkins@nexusclaim.com');
  const [password, setPassword] = useState('••••••••••••');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
    }, 600);
  };

  const handleQuickLogin = (roleEmail: string) => {
    setEmail(roleEmail);
    setIsLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
    }, 500);
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-100 flex items-center justify-center p-4 lg:p-8 relative overflow-hidden">
      {/* Background Glow Accents */}
      <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-indigo-600/20 blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-purple-600/20 blur-3xl"></div>

      <div className="w-full max-w-5xl glass-panel rounded-3xl overflow-hidden grid grid-cols-1 lg:grid-cols-2 shadow-2xl border border-slate-800 relative z-10">
        
        {/* Left Side: Login Form */}
        <div className="p-8 lg:p-12 flex flex-col justify-between bg-slate-900/90 backdrop-blur-xl">
          <div>
            {/* Branding */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-lg text-white tracking-tight">NexusClaim</span>
                <span className="ml-2 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  Enterprise Portal
                </span>
              </div>
            </div>

            <div className="mt-8">
              <h1 className="text-2xl font-extrabold text-white tracking-tight">Sign in to Claim Portal</h1>
              <p className="text-xs text-slate-400 mt-1">Access the Agentic AI Copilot workspace for claim support officers.</p>
            </div>

            {/* Quick Demo Preset Buttons */}
            <div className="mt-6 p-3 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-2">
              <p className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Quick Demo Access:</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('s.jenkins@nexusclaim.com')}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-[11px] font-semibold transition-all text-left truncate"
                >
                  Officer Sarah Jenkins
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('m.thorne@nexusclaim.com')}
                  className="px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-300 text-[11px] font-semibold transition-all text-left truncate"
                >
                  Lead Adjuster M. Thorne
                </button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Work Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300">Password</label>
                  <a href="#forgot" className="text-[11px] font-medium text-indigo-400 hover:underline">Forgot password?</a>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-400">
                  <input type="checkbox" defaultChecked className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500" />
                  <span>Remember this device</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.01]"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                    Authenticating SSO...
                  </span>
                ) : (
                  <>
                    <span>Enter Officer Dashboard</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800 text-center">
            <p className="text-[11px] text-slate-500">
              Strictly Internal Access Only. Secured via SSO & Multi-Factor Hardware Tokens.
            </p>
          </div>
        </div>

        {/* Right Side: Feature Illustration & Agent Showcase */}
        <div className="p-8 lg:p-12 bg-gradient-to-br from-indigo-950/60 via-slate-900 to-purple-950/40 border-t lg:border-t-0 lg:border-l border-slate-800 flex flex-col justify-between relative overflow-hidden">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>Multi-Agent Swarm V3.4</span>
            </div>

            <h2 className="text-3xl font-extrabold text-white leading-tight">
              Intelligent Claim Intake, RAG Policy Match & Fraud Engine
            </h2>

            <p className="text-xs text-slate-300 leading-relaxed">
              Empowering insurance officers to process claims 85% faster with automated OCR document parsing, LangMem historical memory graphs, and real-time confidence scores.
            </p>

            {/* Feature Pills */}
            <div className="space-y-3 pt-2">
              {[
                'Automated Document OCR & Field Verification',
                'LangMem Contextual Vector Memory Search',
                'Real-Time Fraud Pattern Detection Engine',
                'Human-in-the-Loop Audit Trace & Decision Logs'
              ].map((feat, idx) => (
                <div key={idx} className="flex items-center gap-2.5 text-xs text-slate-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Floating Metric Card Graphic */}
          <div className="mt-8 p-4 rounded-2xl bg-slate-900/80 border border-indigo-500/30 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-2">
              <span>ACTIVE AGENT PIPELINE</span>
              <span className="text-emerald-400 font-bold">99.4% ACCURACY</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded-xl bg-slate-800/80">
                <span className="block text-lg font-extrabold text-indigo-400">420ms</span>
                <span className="text-[10px] text-slate-400">Avg OCR Speed</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-800/80">
                <span className="block text-lg font-extrabold text-emerald-400">0.94</span>
                <span className="text-[10px] text-slate-400">LangMem Similarity</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-800/80">
                <span className="block text-lg font-extrabold text-purple-400">7</span>
                <span className="text-[10px] text-slate-400">Active Agents</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
