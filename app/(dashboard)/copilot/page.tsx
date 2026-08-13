'use client';

import React, { useState } from 'react';
import { 
  Bot, 
  Send, 
  Sparkles, 
  BrainCircuit, 
  BookOpen, 
  Wrench, 
  User, 
  CheckCircle2, 
  ChevronRight,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Terminal,
  Paperclip
} from 'lucide-react';
import { useClaims } from '@/lib/context/ClaimsContext';

interface Message {
  id: string;
  sender: 'user' | 'copilot';
  timestamp: string;
  text: string;
  thinkingSteps?: string[];
  memories?: { claimId: string; summary: string; score: number }[];
  policies?: { code: string; title: string; text: string }[];
  toolCalls?: { name: string; result: string }[];
}

export default function AICopilotPage() {
  const { claims } = useClaims();
  const [inputQuery, setInputQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-1',
      sender: 'copilot',
      timestamp: '11:40 AM',
      text: 'Hello Officer Sarah Jenkins. I am your Multi-Agent AI Claims Copilot. I can assist with document OCR verification, LangMem historical case retrieval, policy coverage interpretation, and subrogation calculations. How can I assist you with your active claims queue today?',
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const suggestedQuestions = [
    'What is the subrogation recovery potential for Claim CLM-2026-8841?',
    'Verify hospital discharge bill ICD-10 codes for Claim CLM-2026-9014',
    'Search LangMem for past storm damage claims in Austin TX',
    'Summarize fraud risk factors for Vanguard Traders LLC claim'
  ];

  const handleSendMessage = (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: query,
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsTyping(true);

    // Simulate Multi-Agent streaming response
    setTimeout(() => {
      let botResponse: Message = {
        id: `msg-resp-${Date.now()}`,
        sender: 'copilot',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: '',
        thinkingSteps: [
          'Intake Agent: Parsed question for claim reference & subrogation intent.',
          'Memory Agent: Retreived 2 similar highway accident memory vectors.',
          'RAG Agent: Matched Policy Section 4.2B & Subrogation Protocol.',
          'Tool Execution: Called verify_police_report_db & calculate_subrogation_odds.'
        ],
        memories: [
          { claimId: 'CLM-2025-4109', summary: '3-car pileup on I-95. Approved $15,200 payout with 100% third-party subrogation recovery.', score: 0.94 }
        ],
        policies: [
          { code: 'POL-AUTO-SEC-4.2B', title: 'Collision & Subrogation Protocol', text: 'Coverage authorized up to $50,000 subject to deductible deduction and subrogation pursuit.' }
        ],
        toolCalls: [
          { name: 'calculate_subrogation_odds(thirdParty="Geico")', result: 'SUCCESS (95% Odds of full recovery within 45 days)' }
        ]
      };

      if (query.includes('8841') || query.includes('subrogation')) {
        botResponse.text = 'Based on Police Report PA-8841 and Policy POL-AUTO-99824, Claim CLM-2026-8841 has a **95% probability of 100% subrogation recovery** against third-party driver Car #2. I recommend approving the requested payout of **$17,950** ($18,450 estimate minus $500 deductible) and immediately initiating automated subrogation recovery against Geico Insurance.';
      } else if (query.includes('9014') || query.includes('hospital')) {
        botResponse.text = 'Claim CLM-2026-9014 (Elena Rostova) involves an Emergency Inpatient ICU admission for acute STEMI (ICD-10 I21.0). The $42,300 charge is fully verified against St. Jude Hospital EHR. Under Section 2.1E, emergency pre-authorization requirement is waived. **Recommended Payout: $39,800**.';
      } else {
        botResponse.text = `Analyzed your query across active insurance claims and master policy vector indexes. All primary documentation matches policy terms and risk score is within acceptable bounds.`;
      }

      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
    }, 1200);
  };

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col glass-panel rounded-3xl border border-slate-200/80 dark:border-slate-800 overflow-hidden">
      
      {/* Copilot Header */}
      <div className="p-4 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/50 dark:bg-slate-900/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-teal-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-extrabold text-sm text-slate-900 dark:text-white">Enterprise AI Copilot</h2>
              <span className="px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 text-[10px] font-bold border border-purple-500/20">
                GPT-4o + Multi-Agent Engine
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">LangMem Memory Graph & Real-Time Policy RAG Active</p>
          </div>
        </div>

        <button
          onClick={() => setMessages([messages[0]])}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Reset Conversation"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-3xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/20'
              }`}
            >
              {msg.sender === 'user' ? 'SJ' : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble Container */}
            <div className="space-y-3 flex-1">
              <div
                className={`p-4 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-indigo-600 text-white font-medium shadow-md shadow-indigo-600/20'
                    : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                  <span className="font-bold">{msg.sender === 'user' ? 'Officer Sarah' : 'AI Copilot'}</span>
                  <span>{msg.timestamp}</span>
                </div>
                <div className="prose dark:prose-invert text-xs space-y-2">
                  <p>{msg.text}</p>
                </div>
              </div>

              {/* Agent Thinking Timeline */}
              {msg.thinkingSteps && msg.thinkingSteps.length > 0 && (
                <div className="p-3 rounded-xl bg-slate-100/70 dark:bg-slate-950/70 border border-slate-200/80 dark:border-slate-800/80 space-y-2 text-[11px]">
                  <div className="flex items-center gap-1.5 text-purple-500 font-bold text-[10px] uppercase tracking-wider">
                    <Sparkles className="w-3 h-3 animate-pulse" />
                    <span>Agent Execution Trace ({msg.thinkingSteps.length} steps)</span>
                  </div>
                  <div className="space-y-1 text-slate-500 dark:text-slate-400 font-mono">
                    {msg.thinkingSteps.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Retrieved Memory Cards */}
              {msg.memories && msg.memories.length > 0 && (
                <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/20 space-y-1.5 text-[11px]">
                  <div className="flex items-center gap-1.5 text-purple-400 font-bold text-[10px] uppercase tracking-wider">
                    <BrainCircuit className="w-3 h-3" />
                    <span>LangMem Node Retrieved</span>
                  </div>
                  {msg.memories.map((m, i) => (
                    <div key={i} className="flex items-center justify-between text-slate-300">
                      <span className="font-mono font-bold text-indigo-400">{m.claimId}:</span>
                      <span className="truncate ml-2 text-slate-400">{m.summary}</span>
                      <span className="font-bold text-purple-400 ml-2">{(m.score * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Tool Execution Logs */}
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-[11px] font-mono space-y-1">
                  <div className="flex items-center gap-1.5 text-teal-400 font-bold text-[10px] uppercase tracking-wider">
                    <Terminal className="w-3 h-3" />
                    <span>Tool Execution Result</span>
                  </div>
                  {msg.toolCalls.map((t, i) => (
                    <div key={i} className="text-slate-300">
                      <span className="text-indigo-400 font-bold">&gt; {t.name}:</span> {t.result}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
              <span>Copilot swarm agents are reasoning and searching vector indexes...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Starter Questions */}
      <div className="px-6 py-2 border-t border-slate-200/60 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-950/40 flex items-center gap-2 overflow-x-auto scrollbar-none">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 shrink-0">Prompts:</span>
        {suggestedQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(q)}
            className="px-3 py-1 rounded-full bg-white dark:bg-slate-900 hover:bg-indigo-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all whitespace-nowrap shrink-0"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-3"
        >
          <button
            type="button"
            className="p-2.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Attach File"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask Copilot about any claim, policy clause, subrogation rule, or document OCR..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:outline-none transition-all"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || isTyping}
            className="p-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white shadow-md shadow-purple-600/20 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
