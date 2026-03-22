// ── Agents Panel ───────────────────────────────────────
// Right panel — live agent activity monitor.
// ───────────────────────────────────────────────────────

import React from 'react';
import { useAgentsStore } from '../../stores/agents.store';
import type { AgentId } from '@dexpert/types';
import { Bot, Cpu, Globe, Terminal, Activity, Zap } from 'lucide-react';

const agentMeta: Record<AgentId, { label: string; icon: any; color: string; desc: string }> = {
  planner: { 
    label: 'Dexpert', 
    icon: Bot,
    color: 'text-violet-500', 
    desc: 'Planning & Strategy' 
  },
  browser: { 
    label: 'Web Agent', 
    icon: Globe,
    color: 'text-teal-500', 
    desc: 'Research & Navigation' 
  },
  os: { 
    label: 'OS Agent', 
    icon: Terminal,
    color: 'text-amber-500', 
    desc: 'System Interaction' 
  },
};

const statusConfig: Record<string, { label: string; color: string; dotClass: string }> = {
  idle: { label: 'Idle', color: 'text-zinc-500', dotClass: 'bg-zinc-400' },
  running: { label: 'Thinking', color: 'text-violet-500', dotClass: 'bg-violet-500 animate-pulse-dot' },
  error: { label: 'Error', color: 'text-red-500', dotClass: 'bg-red-500' },
  waiting: { label: 'Waiting', color: 'text-amber-500', dotClass: 'bg-amber-400 animate-pulse' },
};

export function AgentsPanel() {
  const agentStatuses = useAgentsStore((s) => s.agentStatuses);
  const toolCallLog = useAgentsStore((s) => s.toolCallLog);

  return (
    <div className="flex h-full flex-col bg-zinc-50 dark:bg-[#09090b]">
      {/* Header */}
      <div className="px-6 py-5 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-2 mb-1">
          <Activity className="w-4 h-4 text-violet-500" />
          <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-widest">
            Agent Status
          </h2>
        </div>
        <p className="text-[10px] text-zinc-400 font-medium font-mono">
          System Multi-Agent Runtime (SMART)
        </p>
      </div>

      {/* Agent Activity Cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        {(Object.keys(agentMeta) as AgentId[]).map((agentId) => {
          const meta = agentMeta[agentId];
          const status = agentStatuses[agentId] || 'idle';
          const cfg = statusConfig[status] || statusConfig.idle;
          const Icon = meta.icon;

          return (
            <div
              key={agentId}
              className={`group p-4 rounded-2xl border transition-all duration-300 ${
                status === 'running'
                  ? 'bg-white dark:bg-zinc-900 border-violet-500/30 shadow-lg shadow-violet-500/10'
                  : 'bg-white/50 dark:bg-zinc-900/40 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl bg-zinc-100 dark:bg-zinc-800 transition-colors ${status === 'running' ? 'text-violet-500' : 'text-zinc-400'}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">
                      {meta.label}
                    </h3>
                    <p className="text-[10px] text-zinc-500 font-medium">
                      {meta.desc}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 shadow-inner">
                  <div className={`h-1.5 w-1.5 rounded-full ${cfg.dotClass}`} />
                  <span className={`text-[9px] font-bold uppercase tracking-wider ${cfg.color}`}>
                    {cfg.label}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Real-time Event Stream */}
      <div className="mt-auto border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-black/20">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-3.5 h-3.5 text-zinc-400" />
            <h3 className="text-[11px] font-bold text-zinc-500 uppercase tracking-widest">
              Live Event Stream
            </h3>
          </div>
          <span className="text-[10px] font-bold py-0.5 px-2 bg-zinc-200 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 rounded-full">
            {toolCallLog.length}
          </span>
        </div>
        
        <div className="max-h-56 overflow-y-auto px-4 pb-4 space-y-2 custom-scrollbar font-mono">
          {toolCallLog.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-[10px] text-zinc-400 italic">Listening for events...</p>
            </div>
          ) : (
            [...toolCallLog].reverse().slice(0, 15).map((call, idx) => (
              <div key={call.id || idx} className="flex gap-3 text-[10px] animate-in slide-in-from-bottom duration-300">
                <span className="text-zinc-400 shrink-0">[{new Date().toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })}]</span>
                <span className="text-violet-500 font-bold uppercase">{call.agentId || 'SYS'}</span>
                <span className="text-zinc-600 dark:text-zinc-300 truncate">
                   Executing <span className="text-teal-500 font-bold">{call.name}</span>
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
