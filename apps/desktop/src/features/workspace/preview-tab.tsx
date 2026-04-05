// ── Preview Tab (v2) ──────────────────────────────────
// Sandbox environment for rendering agent-created HTML/React.
// Supports safe iframe-based live previews and asset display.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { 
  Globe, Shield, RefreshCcw, ExternalLink, 
  Monitor, Smartphone, Tablet, Search, Lock
} from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspace.store';

export function PreviewTab() {
  const previewUrl = useWorkspaceStore(s => s.previewUrl);
  const [device, setDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [isLoading, setIsLoading] = useState(true);

  if (!previewUrl) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-24 text-center select-none animate-in fade-in zoom-in duration-700 bg-white dark:bg-zinc-950">
        <div className="relative group grayscale hover:grayscale-0 transition-all duration-700">
           <div className="absolute inset-0 bg-violet-500 blur-3xl opacity-0 group-hover:opacity-20 transition-opacity" />
           <div className="p-8 rounded-[48px] bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xl relative z-10 transition-transform hover:scale-105 active:scale-95">
              <Globe className="w-16 h-16 text-zinc-300 dark:text-zinc-800" />
           </div>
        </div>
        <h3 className="text-xl font-black text-zinc-900 dark:text-zinc-50 tracking-tighter mt-12 mb-4">Awaiting Preview Signal</h3>
        <p className="text-sm font-bold text-zinc-400 dark:text-zinc-600 uppercase tracking-widest leading-relaxed max-w-sm italic">Connect a local server or open an HTML file to see the interactive sandbox.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-zinc-50 dark:bg-zinc-950 overflow-hidden h-full relative">
      {/* Sandbox Control Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-zinc-950 border-b border-zinc-200 dark:border-zinc-800 z-40 fixed top-0 left-0 right-0 shadow-lg shadow-zinc-900/5">
        <div className="flex items-center gap-4 flex-1">
           <div className="flex items-center gap-1.5 p-1 px-3 bg-zinc-100 dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-inner group">
              <Lock className="w-3.5 h-3.5 text-emerald-500 opacity-60" />
              <input 
                 type="text" 
                 value={previewUrl} 
                 readOnly 
                 className="bg-transparent text-[11px] font-black text-zinc-600 dark:text-zinc-400 outline-none w-64 tracking-tight" 
              />
           </div>
           <button className="p-2.5 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-all transform active:rotate-180 duration-500">
              <RefreshCcw className="w-4 h-4" />
           </button>
        </div>

        {/* Viewport Control */}
        <div className="flex items-center gap-2 p-1.5 bg-zinc-100 dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800">
           <DeviceBtn active={device === 'mobile'} onClick={() => setDevice('mobile')} icon={Smartphone} />
           <DeviceBtn active={device === 'tablet'} onClick={() => setDevice('tablet')} icon={Tablet} />
           <DeviceBtn active={device === 'desktop'} onClick={() => setDevice('desktop')} icon={Monitor} />
        </div>

        <div className="flex items-center gap-3 ml-4">
           <button className="flex items-center gap-2.5 px-6 py-2.5 rounded-2xl bg-violet-600 text-white text-[11px] font-black tracking-tight shadow-xl shadow-violet-900/40 hover:bg-violet-700 transition-all active:scale-95 group">
              <ExternalLink className="w-3.5 h-3.5 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
              LIVE URL
           </button>
        </div>
      </div>

      {/* Device Simulation Layer */}
      <div className="flex-1 flex items-center justify-center p-12 mt-20 relative z-30">
        <div 
          className={`bg-white shadow-[0_24px_48px_rgba(0,0,0,0.1)] transition-all duration-700 ease-[cubic-bezier(0.83,0,0.17,1)] relative overflow-hidden rounded-[40px] border-8 border-zinc-900 dark:border-zinc-800
             ${device === 'mobile' ? 'w-[375px] h-[667px]' : ''}
             ${device === 'tablet' ? 'w-[768px] h-[1024px]' : ''}
             ${device === 'desktop' ? 'w-full h-full' : ''}
          `}
        >
           {isLoading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 z-50">
                 <div className="w-12 h-12 border-4 border-violet-500/20 border-t-violet-600 rounded-full animate-spin mb-4" />
                 <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Warping Sandbox...</span>
              </div>
           )}
           <iframe 
             src={previewUrl} 
             className="w-full h-full border-none"
             onLoad={() => setIsLoading(false)}
             title="Sandbox Sandbox"
           />
        </div>
      </div>

      {/* Decorative Background Effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-5 dark:opacity-10">
         <div className="absolute top-0 right-0 w-[50%] h-[50%] bg-violet-500 blur-[200px]" />
         <div className="absolute bottom-0 left-0 w-[50%] h-[50%] bg-sky-500 blur-[200px]" />
      </div>
    </div>
  );
}

function DeviceBtn({ active, onClick, icon: Icon }: any) {
  return (
    <button
      onClick={onClick}
      className={`p-2.5 rounded-xl transition-all duration-300 
        ${active 
          ? 'bg-white dark:bg-zinc-950 text-violet-600 dark:text-violet-400 shadow-md ring-1 ring-zinc-200 dark:ring-zinc-800' 
          : 'text-zinc-400 dark:text-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-300'
        }`}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}
