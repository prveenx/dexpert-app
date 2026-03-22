// ── Markdown Renderer ──────────────────────────────────
// Centralized ReactMarkdown config for all message rendering.
// Used by: agent-response.tsx, user-bubble.tsx
// ───────────────────────────────────────────────────────

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  Copy, Check, Code2, ExternalLink
} from 'lucide-react';

// ── Code Block ────────────────────────────────────────

interface CodeBlockProps {
  language: string;
  filename?: string;
  code: string;
  isStreaming?: boolean;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, filename, code, isStreaming }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`group relative my-4 w-full rounded-xl overflow-hidden border transition-all
        ${isStreaming
          ? 'border-violet-400/50 dark:border-violet-500/50 ring-1 ring-violet-500/10 bg-white dark:bg-zinc-900'
          : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-[#09090b] hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md'
        }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-white dark:bg-zinc-900 border-b border-inherit">
        <div className="flex items-center gap-2">
          <div className={`p-1 rounded ${isStreaming ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-600' : 'bg-zinc-100 dark:bg-zinc-800 text-blue-500'}`}>
            <Code2 className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wide">
            {filename || language || 'Code'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-md text-zinc-400 hover:text-green-500 transition-colors"
          title="Copy Code"
        >
          {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Code Preview */}
      <div className="relative p-4 font-mono text-xs text-zinc-600 dark:text-zinc-400 bg-zinc-50/50 dark:bg-black/40 max-h-96 overflow-auto custom-scrollbar">
        <pre className="whitespace-pre-wrap break-words">{code}</pre>
      </div>
    </div>
  );
};

// ── Markdown Components ───────────────────────────────

function createMarkdownComponents() {
  return {
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)(?::(.*))?/.exec(className || '');
      const language = match ? match[1] : 'text';
      const filename = match ? match[2] : undefined;
      const codeContent = String(children).replace(/\n$/, '');

      if (!inline && match) {
        return (
          <CodeBlock
            language={language}
            filename={filename}
            code={codeContent}
          />
        );
      }
      return (
        <code
          className="bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600 dark:text-pink-400 border border-zinc-200 dark:border-zinc-700"
          {...props}
        >
          {children}
        </code>
      );
    },
    p: ({ children }: any) => (
      <p className="mb-3 last:mb-0 leading-7 text-zinc-800 dark:text-zinc-200">{children}</p>
    ),
    ul: ({ children }: any) => (
      <ul className="list-disc pl-5 mb-3 space-y-1 text-zinc-800 dark:text-zinc-200">{children}</ul>
    ),
    ol: ({ children }: any) => (
      <ol className="list-decimal pl-5 mb-3 space-y-1 text-zinc-800 dark:text-zinc-200">{children}</ol>
    ),
    li: ({ children }: any) => <li className="pl-1">{children}</li>,
    a: ({ href, children }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-violet-600 dark:text-violet-400 hover:underline inline-flex items-center gap-0.5"
      >
        {children} <ExternalLink className="w-3 h-3" />
      </a>
    ),
    blockquote: ({ children }: any) => (
      <blockquote className="border-l-4 border-violet-300 dark:border-violet-700 pl-4 py-1 my-3 bg-violet-50 dark:bg-violet-900/10 rounded-r text-zinc-700 dark:text-zinc-400 italic">
        {children}
      </blockquote>
    ),
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-4 rounded-lg border border-zinc-200 dark:border-zinc-700">
        <table className="min-w-full text-sm">{children}</table>
      </div>
    ),
    thead: ({ children }: any) => (
      <thead className="bg-zinc-100 dark:bg-zinc-800">{children}</thead>
    ),
    th: ({ children }: any) => (
      <th className="px-4 py-2 text-left font-semibold text-zinc-900 dark:text-zinc-100 border-b dark:border-zinc-700">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="px-4 py-2 border-b last:border-0 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300">
        {children}
      </td>
    ),
    h1: ({ children }: any) => <h1 className="text-2xl font-bold mb-4 mt-6 text-zinc-900 dark:text-zinc-100">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-xl font-bold mb-3 mt-5 text-zinc-900 dark:text-zinc-100">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-lg font-semibold mb-2 mt-4 text-zinc-900 dark:text-zinc-100">{children}</h3>,
    hr: () => <hr className="my-6 border-zinc-200 dark:border-zinc-800" />,
  };
}

// ── Main Renderer ─────────────────────────────────────

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const mdComponents = createMarkdownComponents();

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
}) => {
  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={mdComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export { CodeBlock };
