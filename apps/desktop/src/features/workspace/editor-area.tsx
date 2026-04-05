// ── Editor Area (v2) ──────────────────────────────────
// High-performance code display and surgical diff engine.
// Integrated with Monaco/Xterm for premium IDE feel.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { 
  Code2, GitBranch, Split, Check, Copy, Maximize2, 
  Terminal, Search, FileCode, Edit3
} from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspace.store';

export function EditorArea() {
  const activeTabId = useWorkspaceStore(s => s.activeEditorTab);
  const openTabs = useWorkspaceStore(s => s.openEditorTabs);
  const files = useWorkspaceStore(s => s.files);
  const closeTab = useWorkspaceStore(s => s.closeEditorTab);
  const setActiveTab = useWorkspaceStore(s => s.setActiveEditor);
  const viewMode = useWorkspaceStore(s => s.editorViewMode);
  const setViewMode = useWorkspaceStore(s => s.setEditorViewMode);

  const activeFile = activeTabId ? files[activeTabId] : null;
  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    if (activeFile) {
      navigator.clipboard.writeText(activeFile.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!activeFile) {
    return (
       <div className="flex-1 flex flex-col items-center justify-center p-24 text-center dark:bg-zinc-950/20 backdrop-blur-3xl select-none group">
         <div className="p-8 rounded-[40px] bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-2xl transition-all duration-700 group-hover:scale-105 group-hover:rotate-1">
            <Code2 className="w-16 h-16 text-zinc-300 dark:text-zinc-800" />
         </div>
         <h2 className="text-xl font-black text-zinc-900 dark:text-zinc-50 tracking-tighter mt-8 mb-3">Initialize Workspace</h2>
         <p className="text-sm text-zinc-500 max-w-[280px] leading-relaxed font-bold italic uppercase tracking-widest opacity-60">Ready to execute AI-driven operations.</p>
       </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-zinc-950">
      {/* Editor Tab Bar */}
      <div className="flex items-center px-4 pt-4 pb-2 bg-zinc-50/50 dark:bg-zinc-900/30 border-b border-zinc-200 dark:border-zinc-800 gap-1 overflow-x-auto custom-scrollbar no-scrollbar scroll-smooth">
        {openTabs.map(path => {
          const file = files[path];
          const isActive = activeTabId === path;
          return (
             <div 
               key={path}
               onClick={() => setActiveTab(path)}
               className={`group flex items-center gap-3 px-6 py-3.5 cursor-pointer rounded-t-2xl transition-all duration-300 relative border-t-2
                 ${isActive 
                    ? 'bg-white dark:bg-zinc-950 border-violet-500 text-zinc-900 dark:text-zinc-50 shadow-[0_-8px_30px_rgb(0,0,0,0.12)]' 
                    : 'border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'
                 }`}
             >
                <div className={`p-1.5 rounded-lg transition-colors ${isActive ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400' : 'bg-transparent text-zinc-400 group-hover:text-zinc-600'}`}>
                   <FileCode className="w-3.5 h-3.5" />
                </div>
                <span className={`text-[12px] font-black tracking-tight ${isActive ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}>
                   {file?.name || 'Untitled'}
                </span>
                <button 
                  onClick={(e) => { e.stopPropagation(); closeTab(path); }}
                  className="ml-3 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all"
                >
                   <Maximize2 className="w-2.5 h-2.5 rotate-45" />
                </button>
             </div>
          );
        })}
      </div>

      {/* Editor Toolbar */}
      <div className="flex items-center justify-between px-8 py-4 border-b border-zinc-100 dark:border-zinc-800/60 bg-white dark:bg-zinc-950 z-20">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 p-1 bg-zinc-100 dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800">
               <ToolbarButton active={viewMode === 'code'} onClick={() => setEditorViewMode('code')} label="Source" icon={Code2} />
               {activeFile.diff && (
                  <ToolbarButton active={viewMode === 'diff'} onClick={() => setEditorViewMode('diff')} label="Surgical Diff" icon={Split} />
               )}
            </div>
            <div className="h-4 w-[1px] bg-zinc-200 dark:bg-zinc-800 mx-2" />
            <div className="flex items-center gap-2">
               <span className="text-[10px] font-black text-zinc-400 dark:text-zinc-600 uppercase tracking-widest">{activeFile.language} Mode</span>
               <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
            </div>
         </div>

         <div className="flex items-center gap-2">
             <button
               onClick={copyCode}
               className="flex items-center gap-2.5 px-4 py-2 rounded-xl bg-zinc-100 dark:bg-zinc-900 hover:bg-zinc-200 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 transition-all"
             >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 text-zinc-500" />}
                <span className="text-[11px] font-black text-zinc-600 dark:text-zinc-400 tracking-tight">{copied ? 'Copied System Clipboard' : 'Copy'}</span>
             </button>
             <button className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl shadow-xl shadow-violet-900/20 transition-all transform active:scale-95 flex items-center gap-2">
                <Edit3 className="w-3.5 h-3.5" />
                <span className="text-[11px] font-black tracking-tight">Manual Edit</span>
             </button>
         </div>
      </div>

      {/* Main Content Pane */}
      <div className="flex-1 relative overflow-auto custom-scrollbar bg-white dark:bg-zinc-950 p-8 pt-12">
          {viewMode === 'code' ? (
             <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
                <pre className="font-mono text-[13px] text-zinc-800 dark:text-zinc-300 leading-relaxed whitespace-pre selection:bg-violet-500/20">
                  {activeFile.content}
                </pre>
             </div>
          ) : (
             <div className="max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
                <pre className="font-mono text-[13px] text-zinc-800 dark:text-zinc-300 leading-relaxed whitespace-pre">
                   {activeFile.diff || activeFile.content}
                </pre>
             </div>
          )}
          
          {/* Glassmorphic safe area at bottom */}
          <div className="h-32" />
      </div>
    </div>
  );

  function setEditorViewMode(mode: 'code' | 'diff' | 'preview') {
    useWorkspaceStore.getState().setEditorViewMode(mode);
  }
}

function ToolbarButton({ active, onClick, label, icon: Icon }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-[11px] font-black tracking-tight transition-all
        ${active 
          ? 'bg-white dark:bg-zinc-950 text-violet-600 dark:text-violet-400 shadow-md transform scale-105 active:scale-100 ring-1 ring-zinc-200 dark:ring-zinc-800' 
          : 'text-zinc-400 dark:text-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-300'
        }`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}
