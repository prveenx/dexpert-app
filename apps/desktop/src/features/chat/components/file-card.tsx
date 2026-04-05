// ── File Card ──────────────────────────────────────────
// Shown inline in chat when an agent creates a new file.
// Displays filename, language badge, and content preview.
// Clicking opens the file in the workspace panel.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { FileCode2, ChevronRight, Plus, ExternalLink } from 'lucide-react';
import { useWorkspaceStore } from '../../../stores/workspace.store';

interface FileCardProps {
  filePath: string;
  language: string;
  contentPreview: string;
  agentId?: string;
}

const langColors: Record<string, string> = {
  typescript: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  javascript: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  python: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  rust: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  html: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
  css: 'bg-violet-500/15 text-violet-400 border-violet-500/20',
  json: 'bg-amber-500/15 text-amber-300 border-amber-500/20',
  markdown: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/20',
  yaml: 'bg-pink-500/15 text-pink-400 border-pink-500/20',
  bash: 'bg-lime-500/15 text-lime-400 border-lime-500/20',
  text: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/20',
};

export const FileCard: React.FC<FileCardProps> = ({
  filePath,
  language,
  contentPreview,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const openEditorTab = useWorkspaceStore(s => s.openEditorTab);
  const openPanel = useWorkspaceStore(s => s.openPanel);
  const setActiveTab = useWorkspaceStore(s => s.setActiveTab);

  const fileName = filePath.replace(/\\/g, '/').split('/').pop() || filePath;
  const dirPath = filePath.replace(/\\/g, '/').split('/').slice(0, -1).join('/');
  const colorClass = langColors[language] || langColors.text;
  const lines = contentPreview.split('\n');
  const previewLines = isExpanded ? lines : lines.slice(0, 8);
  const hasMore = lines.length > 8;

  const handleOpenInPanel = () => {
    openEditorTab(filePath);
    openPanel();
    setActiveTab('files');
  };

  return (
    <div className="w-full my-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="border border-emerald-500/20 rounded-xl overflow-hidden bg-emerald-500/[0.03] hover:bg-emerald-500/[0.06] transition-colors">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-emerald-500/[0.05] border-b border-emerald-500/10">
          <div className="flex items-center gap-2.5">
            <div className="p-1 rounded-md bg-emerald-500/10">
              <Plus className="w-3.5 h-3.5 text-emerald-500" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-zinc-200 tracking-tight">
                {fileName}
              </span>
              <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${colorClass}`}>
                {language}
              </span>
            </div>
            {dirPath && (
              <span className="text-[10px] text-zinc-500 font-mono truncate max-w-48">
                {dirPath}/
              </span>
            )}
          </div>
          <button
            onClick={handleOpenInPanel}
            className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-all"
          >
            <ExternalLink className="w-3 h-3" />
            Open
          </button>
        </div>

        {/* Code Preview */}
        <div className="px-4 py-3 font-mono text-xs">
          <pre className="text-zinc-400 leading-5 whitespace-pre-wrap overflow-hidden">
            {previewLines.map((line, i) => (
              <div key={i} className="flex">
                <span className="inline-block w-8 text-right mr-4 text-zinc-600 select-none shrink-0">
                  {i + 1}
                </span>
                <span className="break-all">{line}</span>
              </div>
            ))}
          </pre>
          {hasMore && !isExpanded && (
            <button
              onClick={() => setIsExpanded(true)}
              className="flex items-center gap-1 mt-2 text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <ChevronRight className="w-3 h-3" />
              <span>{lines.length - 8} more lines...</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
