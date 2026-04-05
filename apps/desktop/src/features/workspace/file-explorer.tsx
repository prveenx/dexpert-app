// ── File Explorer (v2) ────────────────────────────────
// Recursive tree view for the dynamic workspace panel.
// Displays workspace files and folders with status icons.
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import { 
  Folder, FolderOpen, FileCode, FileText, FileJson, 
  ChevronRight, ChevronDown, Plus, Globe, Search, MoreVertical
} from 'lucide-react';
import { useWorkspaceStore, FileTreeNode } from '../../stores/workspace.store';

export function FileExplorer() {
  const fileTree = useWorkspaceStore(s => s.fileTree);
  const toggleTreeNode = useWorkspaceStore(s => s.toggleTreeNode);
  const openEditorTab = useWorkspaceStore(s => s.openEditorTab);
  const activeEditorTab = useWorkspaceStore(s => s.activeEditorTab);

  const renderNode = (node: FileTreeNode, depth: number = 0) => {
    const isFile = node.type === 'file';
    const isExpanded = node.isExpanded;
    const isActive = activeEditorTab === node.path;

    const icon = isFile 
      ? getFileIcon(node.name, node.language)
      : (isExpanded ? <FolderOpen className="w-4 h-4 text-violet-500" /> : <Folder className="w-4 h-4 text-violet-400" />);

    return (
      <div key={node.path} className="group/node select-none">
        <div 
          onClick={() => isFile ? openEditorTab(node.path) : toggleTreeNode(node.path)}
          className={`flex items-center gap-2 py-2 px-6 cursor-pointer transition-all duration-200 border-l-2
            ${isActive 
              ? 'bg-violet-500/10 dark:bg-violet-900/10 border-violet-500 text-violet-600 dark:text-violet-400 font-black' 
              : 'border-transparent text-zinc-500 dark:text-zinc-600 hover:bg-zinc-100 dark:hover:bg-zinc-800/40 hover:text-zinc-900 dark:hover:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700'
            }`}
          style={{ paddingLeft: `${depth * 16 + 24}px` }}
        >
          {!isFile && (
            <div className={`p-0.5 transition-transform duration-300 ${isExpanded ? 'rotate-90' : ''}`}>
              <ChevronRight className={`w-3 h-3 ${isActive ? 'text-violet-500' : 'text-zinc-400'}`} />
            </div>
          )}
          <div className="shrink-0">{icon}</div>
          <span className={`text-[13px] truncate ${isFile ? 'font-bold tracking-tight' : 'font-extrabold uppercase tracking-widest opacity-80'}`}>
            {node.name}
          </span>
          
          {/* Status Indicators */}
          {node.status && node.status !== 'unchanged' && (
            <div className={`w-1.5 h-1.5 rounded-full ml-auto shadow-sm animate-pulse ${
              node.status === 'new' ? 'bg-emerald-500' : 
              node.status === 'modified' ? 'bg-violet-500' : 
              'bg-red-500'
            }`} title={node.status.toUpperCase()} />
          )}

          {!node.status || node.status === 'unchanged' && (
             <MoreVertical className="w-3.5 h-3.5 ml-auto opacity-0 group-hover/node:opacity-50 transition-opacity hover:opacity-100" />
          )}
        </div>
        
        {isExpanded && node.children && (
          <div className="flex flex-col">
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-transparent">
      {/* Search Header (Inline) */}
      <div className="px-6 pt-4 pb-2">
        <div className="relative group/search text-zinc-400 dark:text-zinc-600 focus-within:text-violet-500 transition-colors">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" />
          <input 
            type="text" 
            placeholder="Search workspace..." 
            className="w-full bg-zinc-100 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl pl-9 pr-2 py-2.5 text-[11px] font-bold tracking-tight outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/10 transition-all placeholder:text-zinc-400 dark:placeholder:text-zinc-700"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar py-4 pb-24">
        {fileTree.length > 0 ? (
          fileTree.map(node => renderNode(node))
        ) : (
          <div className="flex flex-col items-center justify-center h-64 px-12 text-center group">
            <div className="p-4 rounded-3xl bg-zinc-100 dark:bg-zinc-900 mb-6 group-hover:scale-110 transition-transform duration-500">
               <Plus className="w-8 h-8 text-zinc-300 dark:text-zinc-800" />
            </div>
            <h4 className="text-xs font-black text-zinc-500 dark:text-zinc-400 uppercase tracking-widest mb-2">No Sources Found</h4>
            <p className="text-[10px] text-zinc-400 dark:text-zinc-600 italic leading-relaxed">Agent has not created or detected any workspace files in this turn.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function getFileIcon(name: string, language?: string) {
  const ext = name.split('.').pop()?.toLowerCase();
  
  if (['ts', 'tsx', 'js', 'jsx'].includes(ext || '')) return <FileCode className="w-4 h-4 text-sky-500" />;
  if (['json', 'yaml', 'yml'].includes(ext || '')) return <FileJson className="w-4 h-4 text-emerald-500" />;
  if (['html', 'css'].includes(ext || '')) return <Globe className="w-4 h-4 text-rose-500" />;
  if (['md', 'mdx', 'txt', 'py'].includes(ext || '')) return <FileText className="w-4 h-4 text-zinc-400 dark:text-zinc-500" />;
  
  return <FileCode className="w-4 h-4 text-zinc-400 dark:text-zinc-600" />;
}
