// ── Diff View (Inline Chat) ───────────────────────────
// Displays surgical edits made by agents in a clear,
// colored diff format.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { FileEdit, ChevronRight, ChevronDown, ExternalLink } from 'lucide-react';
import { useWorkspaceStore } from '../../../stores/workspace.store';

interface DiffViewProps {
  filePath: string;
  diff: string;
  agentId?: string;
}

export const DiffView: React.FC<DiffViewProps> = ({ filePath, diff }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const openEditorTab = useWorkspaceStore(s => s.openEditorTab);
  const openPanel = useWorkspaceStore(s => s.openPanel);
  const setEditorViewMode = useWorkspaceStore(s => s.setEditorViewMode);

  const fileName = filePath.replace(/\\/g, '/').split('/').pop() || filePath;

  const handleOpenInEditor = () => {
    openEditorTab(filePath);
    setEditorViewMode('diff');
    openPanel();
  };

  const lines = diff.split('\n');
  const visibleLines = isExpanded ? lines : [];

  const renderedLines = visibleLines.map((line, i) => {
    let bgColor = '';
    let textColor = 'text-zinc-400';
    let prefix = ' ';

    if (line.startsWith('+')) {
      bgColor = 'bg-emerald-500/10';
      textColor = 'text-emerald-400';
      prefix = '+';
    } else if (line.startsWith('-')) {
      bgColor = 'bg-rose-500/10';
      textColor = 'text-rose-400';
      prefix = '-';
    } else if (line.startsWith('@@')) {
      textColor = 'text-violet-400 font-bold';
      prefix = ' ';
    }

    // Clean up purely for display
    const displayLine = (line.startsWith('+') || line.startsWith('-')) ? line.slice(1) : line;

    return (
      <div key={i} className={`flex min-h-[1.2rem] px-2 ${bgColor}`}>
        <span className="w-10 text-right mr-4 text-zinc-600 select-none font-mono shrink-0">
          {prefix === ' ' ? '' : prefix}
        </span>
        <span className={`font-mono break-all whitespace-pre-wrap ${textColor}`}>
          {displayLine}
        </span>
      </div>
    );
  });

  return (
    <div className="w-full my-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="border border-violet-500/20 rounded-xl overflow-hidden bg-zinc-900 shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 bg-violet-500/[0.05] border-b border-violet-500/10">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 group"
          >
            <div className="p-1 rounded bg-zinc-800 group-hover:bg-zinc-700 transition-colors">
              {isExpanded ? <ChevronDown className="w-3 h-3 text-zinc-400" /> : <ChevronRight className="w-3 h-3 text-zinc-400" />}
            </div>
            <FileEdit className="w-3.5 h-3.5 text-violet-400" />
            <span className="text-xs font-bold text-zinc-200">
              Edited: {fileName}
            </span>
          </button>
          <button
            onClick={handleOpenInEditor}
            className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold text-violet-400 hover:text-white transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            Analyze Diff
          </button>
        </div>

        {/* Diff Content */}
        {isExpanded && (
          <div className="py-2 text-[11px] leading-relaxed max-h-64 overflow-y-auto custom-scrollbar bg-black/20">
            {renderedLines}
          </div>
        )}
      </div>
    </div>
  );
};
