// ── Markdown Renderer (v2) ───────────────────────────
// Centralized ReactMarkdown config for all message rendering.
// Enhanced for v2: Code highlighting, Mermaid, KaTeX,
// and premium IDE aesthetics.
// ───────────────────────────────────────────────────────

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import mermaid from 'mermaid';
import {
  Copy, Check, Code2, ExternalLink, Play, Search, Maximize2
} from 'lucide-react';

// Initialize mermaid for premium diagrams
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#8b5cf6',
    primaryTextColor: '#fff',
    primaryBorderColor: '#7c3aed',
    lineColor: '#52525b',
    secondaryColor: '#1e1b4b',
    tertiaryColor: '#111827'
  }
});

// ── Mermaid Block ─────────────────────────────────────
const MermaidBlock: React.FC<{ code: string }> = ({ code }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      try {
        const id = `mermaid-${crypto.randomUUID().slice(0, 8)}`;
        const { svg } = await mermaid.render(id, code);
        setSvg(svg);
      } catch (err: any) {
        setError(err.message);
      }
    };
    renderDiagram();
  }, [code]);

  if (error) return <div className="text-red-400 text-xs italic p-4 bg-red-950/20 rounded-xl my-4">Mermaid Syntax Error: {error}</div>;
  
  return (
    <div 
      ref={containerRef}
      className="my-6 p-6 bg-zinc-900 border border-zinc-800 rounded-2xl overflow-x-auto flex flex-col items-center shadow-inner"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};

// ── Code Block (Enhanced) ────────────────────────────
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
      className={`group relative my-6 w-full rounded-2xl overflow-hidden border transition-all duration-300
        ${isStreaming
          ? 'border-violet-500/50 ring-1 ring-violet-500/20 bg-zinc-950 shadow-violet-900/10 shadow-2xl'
          : 'border-zinc-800 bg-zinc-950 hover:border-violet-500/30'
        }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/40 backdrop-blur-md border-b border-zinc-800">
        <div className="flex items-center gap-2.5">
          <div className="p-1 px-2 rounded-lg bg-zinc-800/80 text-violet-400 flex items-center gap-2">
            <Code2 className="w-3.5 h-3.5" />
            <span className="text-[10px] font-extrabold uppercase tracking-widest">{language}</span>
          </div>
          {filename && (
            <span className="text-[11px] font-bold text-zinc-500 italic tracking-tight">
              {filename}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
           <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-white transition-all"
            title="Copy Code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="relative p-6 font-mono text-[13px] text-zinc-300 leading-relaxed overflow-auto max-h-[500px] custom-scrollbar">
        <pre className="whitespace-pre-wrap break-words">{code}</pre>
      </div>
    </div>
  );
};

// ── Components Configuration ─────────────────────────
function createMarkdownComponents() {
  return {
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)(?::(.*))?/.exec(className || '');
      const language = match ? match[1] : 'text';
      const filename = match ? match[2] : undefined;
      const codeContent = String(children).replace(/\n$/, '');

      if (!inline && language === 'mermaid') {
        return <MermaidBlock code={codeContent} />;
      }

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
          className="bg-zinc-800/80 px-1.5 py-0.5 rounded text-sm font-bold font-mono text-violet-400 border border-zinc-700/50"
          {...props}
        >
          {children}
        </code>
      );
    },
    p: ({ children }: any) => (
      <p className="mb-4 last:mb-0 leading-8 text-[15px] text-zinc-800 dark:text-zinc-200">{children}</p>
    ),
    ul: ({ children }: any) => (
      <ul className="list-disc pl-5 mb-4 space-y-2 text-zinc-800 dark:text-zinc-200">{children}</ul>
    ),
    ol: ({ children }: any) => (
      <ol className="list-decimal pl-5 mb-4 space-y-2 text-zinc-800 dark:text-zinc-200">{children}</ol>
    ),
    li: ({ children }: any) => <li className="pl-1 leading-normal tracking-tight">{children}</li>,
    a: ({ href, children }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-violet-500 font-bold underline decoration-violet-500/20 hover:decoration-violet-500 transition-all inline-flex items-center gap-0.5"
      >
        {children} <ExternalLink className="w-3 h-3" />
      </a>
    ),
    blockquote: ({ children }: any) => (
      <blockquote className="border-l-4 border-violet-500 pl-6 py-4 my-6 bg-violet-500/5 rounded-r-2xl text-zinc-700 dark:text-zinc-300 italic text-[15px] leading-relaxed shadow-sm">
        {children}
      </blockquote>
    ),
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm bg-white dark:bg-zinc-950">
        <table className="min-w-full text-sm">{children}</table>
      </div>
    ),
    thead: ({ children }: any) => (
      <thead className="bg-zinc-50 dark:bg-zinc-900 shadow-sm uppercase tracking-widest text-[10px] font-extrabold">{children}</thead>
    ),
    th: ({ children }: any) => (
      <th className="px-6 py-4 text-left font-bold text-zinc-900 dark:text-zinc-100 border-b dark:border-zinc-800">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="px-6 py-4 border-b last:border-0 dark:border-zinc-900 text-zinc-700 dark:text-zinc-300">
        {children}
      </td>
    ),
    h1: ({ children }: any) => <h1 className="text-3xl font-black mb-6 mt-10 text-zinc-900 dark:text-zinc-50 tracking-tighter">{children}</h1>,
    h2: ({ children }: any) => <h2 className="text-2xl font-black mb-4 mt-8 text-zinc-900 dark:text-zinc-100 tracking-tight">{children}</h2>,
    h3: ({ children }: any) => <h3 className="text-xl font-bold mb-3 mt-6 text-zinc-900 dark:text-zinc-200 tracking-tight">{children}</h3>,
    hr: () => <hr className="my-10 border-zinc-200 dark:border-zinc-800" />,
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
  const ReactMarkdownAny = ReactMarkdown as any;

  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdownAny
        remarkPlugins={[remarkGfm, remarkMath] as any}
        rehypePlugins={[rehypeKatex] as any}
        components={mdComponents as any}
      >
        {content}
      </ReactMarkdownAny>
    </div>
  );
};

export { CodeBlock };
