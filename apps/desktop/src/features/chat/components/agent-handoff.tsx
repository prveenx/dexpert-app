// ── Agent Handoff (Inline Chat) ──────────────────────────
// Visually transitions the chat context when one agent
// hands off a task to another specialist.
// ───────────────────────────────────────────────────────

import React from 'react';
import { ArrowRightLeft, Bot, Sparkles } from 'lucide-react';

interface AgentHandoffProps {
  fromAgent: string;
  toAgent: string;
  taskSummary: string;
}

const agentDisplayMap: Record<string, { label: string; color: string; bgColor: string }> = {
  planner: { label: 'Dexpert', color: 'text-violet-500', bgColor: 'bg-violet-500/10' },
  os: { label: 'OS Agent', color: 'text-amber-500', bgColor: 'bg-amber-500/10' },
  browser: { label: 'Research Bot', color: 'text-emerald-500', bgColor: 'bg-emerald-500/10' },
};

export const AgentHandoff: React.FC<AgentHandoffProps> = ({ fromAgent, toAgent, taskSummary }) => {
  const from = agentDisplayMap[fromAgent.toLowerCase()] || { label: fromAgent, color: 'text-zinc-400', bgColor: 'bg-zinc-400/10' };
  const to = agentDisplayMap[toAgent.toLowerCase()] || { label: toAgent, color: 'text-zinc-100', bgColor: 'bg-zinc-100/10' };

  return (
    <div className="w-full my-4 px-2 animate-in fade-in slide-in-from-left-2 duration-400">
      <div className="flex flex-col items-center gap-3 py-4 border border-zinc-700/30 rounded-2xl bg-zinc-900/30 backdrop-blur-md shadow-xl">
        <div className="flex items-center gap-6">
          <div className={`p-2.5 rounded-xl ${from.bgColor} ${from.color} border border-transparent shadow-lg`}>
            <Bot className="w-5 h-5" />
          </div>

          <div className="relative flex items-center justify-center">
            <div className="w-12 h-px bg-gradient-to-r from-transparent via-violet-500/50 to-transparent" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="p-1 px-2 bg-zinc-800 rounded-full border border-zinc-700 shadow-xl">
                <ArrowRightLeft className="w-3 h-3 text-violet-400" />
              </div>
            </div>
          </div>

          <div className={`p-2.5 rounded-xl ${to.bgColor} ${to.color} border border-transparent shadow-lg animate-pulse`}>
            <Bot className="w-5 h-5" />
          </div>
        </div>

        <div className="flex flex-col items-center text-center px-6">
          <span className="text-[10px] font-extrabold uppercase tracking-widest text-zinc-500 mb-1">
            Delegating to {to.label}
          </span>
          <p className="text-sm font-medium text-zinc-300 leading-relaxed italic max-w-sm">
            "{taskSummary}"
          </p>
        </div>

        {/* Status Micro-animation */}
        <div className="flex items-center gap-1.5 mt-1 px-3 py-1 bg-violet-500/10 rounded-full border border-violet-500/20">
          <Sparkles className="w-3 h-3 text-violet-400 animate-pulse" />
          <span className="text-[10px] font-bold text-violet-300 uppercase tracking-tighter">
            Specialist Initializing
          </span>
        </div>
      </div>
    </div>
  );
};
