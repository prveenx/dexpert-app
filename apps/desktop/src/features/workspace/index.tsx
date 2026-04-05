// ── Workspace Panel (v2 Consolidated) ────────────────
// Unified entry point for the Dexpert Agentic IDE.
// Triggers on-demand during agent operations.
// ───────────────────────────────────────────────────────

import React, { useState, useEffect } from 'react';
import { 
  X, Files, Play, Terminal, Settings2, Maximize2,
  Minimize2, ChevronLeft, ChevronRight, Code2
} from 'lucide-react';
import { useWorkspaceStore } from '../../stores/workspace.store';
import { FileExplorer } from './file-explorer';
import { EditorArea } from './editor-area';
import { TerminalPanel } from './terminal-panel';
import { PreviewTab } from './preview-tab';

export default function Workspace() {
  const isOpen = useWorkspaceStore(s => s.isOpen);
  const closePanel = useWorkspaceStore(s => s.closePanel);
  const activeTab = useWorkspaceStore(s => s.activeTab);
  const setActiveTab = useWorkspaceStore(s => s.setActiveTab);
  const panelWidth = useWorkspaceStore(s => s.panelWidth);
  const setPanelWidth = useWorkspaceStore(s => s.setPanelWidth);

  const [isResizing, setIsResizing] = useState(false);

  // Close with Escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) closePanel();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, closePanel]);

  // Dynamic Resizing Logic
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      // Calculate panel width from right edge
      const width = ((window.innerWidth - e.clientX) / window.innerWidth) * 100;
      setPanelWidth(width);
    };

    const handleMouseUp = () => setIsResizing(false);

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
    } else {
      document.body.style.cursor = 'default';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, setPanelWidth]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-y-0 right-0 z-50 flex border-l border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-2xl animate-in slide-in-from-right duration-500 ease-in-out"
      style={{ width: `${panelWidth}%` }}
    >
      {/* Precision Resize Handle */}
      <div 
        onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
        className="absolute inset-y-0 -left-1 w-2 cursor-col-resize hover:bg-violet-500/50 transition-colors z-[100]"
      />

      {/* Navigation Rail (Vertical) */}
      <div className="w-16 flex flex-col items-center py-6 bg-zinc-50 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 shrink-0">
        <div className="flex flex-col items-center gap-4">
          <TabButton 
            active={activeTab === 'files'} 
            onClick={() => setActiveTab('files')} 
            icon={Files} 
            tooltip="File Explorer" 
          />
          <TabButton 
            active={activeTab === 'preview'} 
            onClick={() => setActiveTab('preview')} 
            icon={Play} 
            tooltip="Live Preview" 
          />
          <TabButton 
            active={activeTab === 'terminal'} 
            onClick={() => setActiveTab('terminal')} 
            icon={Terminal} 
            tooltip="Environment Terminal" 
          />
        </div>

        <div className="mt-auto flex flex-col items-center gap-4">
           <button 
             className="p-3 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
             title="IDE Settings"
           >
             <Settings2 className="w-5 h-5" />
           </button>
           <button 
             onClick={closePanel}
             className="p-3 text-zinc-400 hover:text-red-500 transition-colors"
             title="Minimize Workspace"
           >
             <ChevronRight className="w-6 h-6" />
           </button>
        </div>
      </div>

      {/* Main Feature Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Contextual Sidebars (Explorer) */}
        {activeTab === 'files' && (
          <div className="w-72 flex flex-col border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30">
            <div className="px-6 py-5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
              <span className="text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-[0.2em]">Workspace Explorer</span>
              <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-1 px-1.5 rounded-md hover:bg-zinc-200 dark:hover:bg-zinc-800 text-[10px] font-bold text-zinc-500">NEW</button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              <FileExplorer />
            </div>
          </div>
        )}

        {/* Action Canvas (Editor, Terminal, Preview) */}
        <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-zinc-950">
          <div className="flex-1 relative overflow-hidden">
             {activeTab === 'files' && <EditorArea />}
             {activeTab === 'preview' && <PreviewTab />}
             {activeTab === 'terminal' && <TerminalPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon: Icon, tooltip }: any) {
  return (
    <button
      onClick={onClick}
      className={`group relative p-3.5 rounded-2xl transition-all duration-300 ${
        active 
          ? 'bg-violet-600 text-white shadow-xl shadow-violet-900/30 scale-110' 
          : 'text-zinc-400 dark:text-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200 dark:hover:bg-zinc-800'
      }`}
      title={tooltip}
    >
      <Icon className="w-5 h-5 stroke-[2.5]" />
      {active && (
        <span className="absolute -left-1 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-white rounded-full transition-transform" />
      )}
    </button>
  );
}
