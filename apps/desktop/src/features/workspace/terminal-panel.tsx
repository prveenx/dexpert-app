// ── Terminal Panel (v2) ───────────────────────────────
// High-performance integrated terminal emulator.
// Displays live shell output and command history.
// ───────────────────────────────────────────────────────

import React, { useRef, useEffect } from 'react';
import { 
  Terminal, Shield, Activity, RotateCcw, 
  Search, Maximize2, X, Command, Cpu, Hash
} from 'lucide-react';
import { useWorkspaceStore, TerminalEntry } from '../../stores/workspace.store';

export function TerminalPanel() {
  const history = useWorkspaceStore(s => s.terminalHistory);
  const clearTerminal = useWorkspaceStore(s => s.clearTerminal);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new entries
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div className="flex-1 flex flex-col bg-zinc-950/80 backdrop-blur-3xl overflow-hidden font-mono shadow-2xl animate-in fade-in duration-700">
      {/* Terminal Command Bar */}
      <div className="flex items-center justify-between px-8 py-5 border-b border-zinc-900 bg-zinc-950/40 z-30">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-zinc-900 rounded-xl border border-zinc-800 shadow-inner group transition-transform hover:scale-105">
             <Terminal className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300" />
          </div>
          <div>
            <h3 className="text-[11px] font-black text-white uppercase tracking-widest leading-none">Persistent Shell</h3>
            <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-tight">Active session at 127.0.0.1</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
             onClick={clearTerminal}
             className="px-4 py-2.5 bg-zinc-900/50 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-[10px] font-black text-zinc-400 hover:text-zinc-200 transition-all flex items-center gap-2 group transform active:scale-95"
          >
             <RotateCcw className="w-3.5 h-3.5 group-hover:rotate-180 transition-transform duration-700" />
             CLEAR LOGS
          </button>
          <div className="h-5 w-[1px] bg-zinc-900 mx-1" />
          <div className="flex items-center bg-zinc-900/80 rounded-full px-3 py-1.5 gap-2 border border-zinc-800/50">
             <Activity className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
             <span className="text-[10px] font-black text-emerald-500/80 uppercase tracking-widest">Connected</span>
          </div>
        </div>
      </div>

      {/* Main Terminal Window */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-8 px-12 custom-scrollbar scroll-smooth bg-zinc-950/20"
      >
        <div className="max-w-6xl mx-auto space-y-8 pb-32">
          {history.length > 0 ? (
            history.map((entry, idx) => (
              <TerminalBlock key={entry.id || idx} entry={entry} />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center pt-32 text-center opacity-30 select-none">
               <Cpu className="w-16 h-16 text-zinc-300 mb-8 animate-pulse" />
               <h4 className="text-[13px] font-black text-zinc-400 uppercase tracking-widest mb-2">Initialize Shell Listener</h4>
               <p className="text-[11px] text-zinc-600 italic font-bold">Standard stream connected and waiting for system commands.</p>
            </div>
          )}
        </div>
      </div>

      {/* Terminal Footer Navigation */}
      <div className="px-8 py-3 bg-zinc-900/40 border-t border-zinc-900 flex items-center justify-between text-[10px] font-black text-zinc-500 tracking-widest">
         <div className="flex items-center gap-6">
            <span className="flex items-center gap-2 hover:text-zinc-300 transition-colors cursor-default">
               <Hash className="w-3.5 h-3.5" /> PTY: NODE-PTY v1.1
            </span>
            <span className="flex items-center gap-2 hover:text-zinc-300 transition-colors cursor-default">
               <Command className="w-3.5 h-3.5" /> SHELL: PWSH CORE
            </span>
         </div>
         <div className="flex items-center gap-4">
            <span className="text-zinc-700">|</span>
            <span className="text-emerald-500/60 uppercase">System Ready</span>
         </div>
      </div>
    </div>
  );
}

function TerminalBlock({ entry }: { entry: TerminalEntry }) {
  return (
    <div className="group animate-in slide-in-from-bottom-2 duration-500">
      {/* Entry Header/Command line */}
      <div className="flex items-center gap-4 mb-3 border-l-2 border-zinc-800 group-hover:border-violet-500 pl-4 py-1 transition-all">
         <span className="shrink-0 text-emerald-500/80 font-black tracking-normal">$</span>
         <span className="text-[13px] font-bold text-zinc-200 tracking-tight glow-violet-sm">{entry.command}</span>
         {entry.exitCode !== undefined && (
            <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-md ml-auto tracking-[0.2em] transform group-hover:scale-105 transition-transform ${entry.exitCode === 0 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500 underline decoration-red-500/20'}`}>
               EXIT: {entry.exitCode}
            </span>
         )}
      </div>

      {/* Entry Output Overlay */}
      <div className="relative ml-8 group-hover:ml-9 transition-all">
         <div className="absolute inset-0 bg-violet-600/5 dark:bg-violet-600/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
         <pre className={`text-[12px] leading-relaxed whitespace-pre-wrap rounded-2xl relative z-10 
            ${entry.isError ? 'text-red-400 font-bold italic opacity-95' : 'text-zinc-400 dark:text-zinc-500 opacity-90 group-hover:opacity-100'} transition-opacity`}>
            {entry.output || <span className="opacity-40 italic font-normal">[Process returned no visible output]</span>}
         </pre>
      </div>
    </div>
  );
}
