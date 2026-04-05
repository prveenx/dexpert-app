// ── Terminal Block ─────────────────────────────────────
// Inline terminal output rendered in the chat thread
// when an agent runs shell commands. Supports ANSI colors
// and collapsible output for long results.
// ───────────────────────────────────────────────────────

import React, { useState, useMemo } from 'react';
import { Terminal, ChevronDown, ChevronRight, Copy, Check, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useWorkspaceStore } from '../../../stores/workspace.store';

interface TerminalBlockProps {
  command: string;
  output: string;
  exitCode?: number;
  isError?: boolean;
  agentId?: string;
}

// Minimal ANSI stripping for plain text fallback
function stripAnsi(str: string): string {
  return str.replace(/\x1b\[[0-9;]*m/g, '');
}

// Convert ANSI codes to styled spans
function parseAnsi(str: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const ansiRegex = /\x1b\[([0-9;]*)m/g;
  let lastIndex = 0;
  let currentClass = '';
  let match: RegExpExecArray | null;

  const colorMap: Record<string, string> = {
    '30': 'text-zinc-600', '31': 'text-red-400', '32': 'text-emerald-400',
    '33': 'text-yellow-400', '34': 'text-blue-400', '35': 'text-violet-400',
    '36': 'text-cyan-400', '37': 'text-zinc-200',
    '90': 'text-zinc-500', '91': 'text-red-300', '92': 'text-emerald-300',
    '93': 'text-yellow-300', '94': 'text-blue-300', '95': 'text-violet-300',
    '96': 'text-cyan-300', '97': 'text-white',
    '1': 'font-bold', '0': '',
  };

  while ((match = ansiRegex.exec(str)) !== null) {
    if (match.index > lastIndex) {
      const text = str.slice(lastIndex, match.index);
      if (text) {
        parts.push(
          <span key={parts.length} className={currentClass || undefined}>{text}</span>
        );
      }
    }

    const codes = match[1].split(';');
    const newClasses: string[] = [];
    for (const code of codes) {
      if (code === '0' || code === '') {
        currentClass = '';
      } else if (colorMap[code]) {
        newClasses.push(colorMap[code]);
      }
    }
    if (newClasses.length) currentClass = newClasses.join(' ');

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < str.length) {
    parts.push(
      <span key={parts.length} className={currentClass || undefined}>
        {str.slice(lastIndex)}
      </span>
    );
  }

  return parts.length > 0 ? parts : [str];
}

export const TerminalBlock: React.FC<TerminalBlockProps> = ({
  command,
  output,
  exitCode,
  isError = false,
  agentId,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [copied, setCopied] = useState(false);
  const setActiveTab = useWorkspaceStore(s => s.setActiveTab);
  const openPanel = useWorkspaceStore(s => s.openPanel);

  const lines = output.split('\n');
  const isTruncated = lines.length > 20;
  const visibleLines = isExpanded ? (isTruncated ? lines.slice(0, 20) : lines) : [];

  const handleCopy = () => {
    navigator.clipboard.writeText(output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenTerminal = () => {
    openPanel();
    setActiveTab('terminal');
  };

  const success = exitCode === 0 || (!isError && exitCode === undefined);
  const headerColor = success
    ? 'bg-zinc-900 border-zinc-700/50'
    : 'bg-red-950/30 border-red-500/20';
  const statusIcon = success
    ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
    : <AlertCircle className="w-3.5 h-3.5 text-red-400" />;

  const renderedLines = useMemo(() =>
    visibleLines.map((line, i) => (
      <div key={i} className="flex min-h-[1.2em]">
        <span className="text-zinc-600 select-none w-7 shrink-0 text-right mr-3 font-mono">
          {i + 1}
        </span>
        <span className="text-zinc-300 break-all whitespace-pre-wrap">
          {parseAnsi(line)}
        </span>
      </div>
    )),
    [visibleLines]
  );

  return (
    <div className="w-full my-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className={`border rounded-xl overflow-hidden ${headerColor}`}>
        {/* Header */}
        <div className={`flex items-center justify-between px-3 py-2 border-b ${headerColor}`}>
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-2 group"
            >
              <div className="p-1 rounded bg-zinc-800 group-hover:bg-zinc-700 transition-colors">
                {isExpanded
                  ? <ChevronDown className="w-3 h-3 text-zinc-400" />
                  : <ChevronRight className="w-3 h-3 text-zinc-400" />
                }
              </div>
              <Terminal className="w-3.5 h-3.5 text-zinc-400" />
              <code className="text-xs text-zinc-200 font-mono">
                $ {command.length > 60 ? command.slice(0, 60) + '…' : command}
              </code>
            </button>
          </div>
          <div className="flex items-center gap-2">
            {statusIcon}
            {exitCode !== undefined && (
              <span className={`text-[9px] font-bold font-mono px-1.5 py-0.5 rounded ${
                exitCode === 0
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : 'bg-red-500/10 text-red-400'
              }`}>
                exit {exitCode}
              </span>
            )}
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 transition-colors"
              title="Copy output"
            >
              {copied
                ? <Check className="w-3 h-3 text-emerald-400" />
                : <Copy className="w-3 h-3" />
              }
            </button>
            <button
              onClick={handleOpenTerminal}
              className="text-[9px] font-bold text-zinc-500 hover:text-zinc-300 px-1.5 py-0.5 rounded hover:bg-zinc-700 transition-colors"
            >
              Panel
            </button>
          </div>
        </div>

        {/* Output */}
        {isExpanded && (
          <div className="px-4 py-3 font-mono text-xs leading-5 max-h-72 overflow-y-auto bg-zinc-950/60 custom-scrollbar">
            {output.trim() ? renderedLines : (
              <span className="text-zinc-600 italic">No output</span>
            )}
            {isTruncated && (
              <div className="mt-2 pt-2 border-t border-zinc-800 text-[10px] text-zinc-500 flex items-center justify-between">
                <span>{lines.length - 20} more lines truncated</span>
                <button
                  onClick={handleOpenTerminal}
                  className="text-violet-400 hover:text-violet-300"
                >
                  View full output in panel →
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
