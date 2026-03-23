import React from 'react';
import { Blocks, Search, Download, Star, ExternalLink, ShieldCheck, Zap } from 'lucide-react';

export function ExtensionsView() {
  const extensions = [
    {
      id: 'browser',
      name: 'Web Surfer',
      description: 'Allows Dexpert to browse the web, search Google, and extract data from websites.',
      version: '1.2.0',
      author: 'Dexpert Team',
      installed: true,
      downloads: '45k',
      rating: 4.9,
    },
    {
      id: 'terminal',
      name: 'Terminal Expert',
      description: 'Execute shell commands, manage files, and run scripts directly from chat.',
      version: '0.9.5',
      author: 'Dexpert Team',
      installed: true,
      downloads: '12k',
      rating: 4.7,
    },
    {
      id: 'python',
      name: 'Python Interpreter',
      description: 'Secure sandbox for executing Python code and data visualization.',
      version: '2.1.0',
      author: 'Dexpert Team',
      installed: false,
      downloads: '89k',
      rating: 4.8,
    },
    {
      id: 'github',
      name: 'GitHub Integration',
      description: 'Manage repositories, create PRs, and review code from the chat.',
      version: '1.0.2',
      author: 'GitHub Inc.',
      installed: false,
      downloads: '150k',
      rating: 4.6,
    }
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-950 animate-in fade-in duration-500">
      <div className="flex-shrink-0 px-8 py-6 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Extensions</h1>
            <p className="text-zinc-500 text-sm mt-1">Supercharge your agents with specialized capabilities.</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input 
                type="text" 
                placeholder="Search extensions..." 
                className="pl-10 pr-4 py-2 bg-zinc-100 dark:bg-zinc-900 border border-transparent focus:border-violet-500/50 rounded-xl text-sm transition-all outline-none w-64"
              />
            </div>
            <button className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-violet-500/20 transition-all">
              Marketplace
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8 bg-zinc-50/50 dark:bg-zinc-900/20 custom-scrollbar">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-6xl mx-auto">
          {extensions.map(ext => (
            <div key={ext.id} className="group bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 hover:shadow-xl hover:shadow-violet-500/5 transition-all duration-300">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-zinc-100 dark:bg-zinc-800 rounded-xl flex items-center justify-center text-violet-600 group-hover:scale-110 transition-transform duration-300">
                  <Blocks className="w-6 h-6" />
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-0.5 text-amber-400">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    <span className="text-xs font-bold text-zinc-600 dark:text-zinc-400">{ext.rating}</span>
                  </div>
                  {ext.installed && (
                    <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2.5 py-1 rounded-full text-[10px] font-bold flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> Installed
                    </span>
                  )}
                </div>
              </div>
              
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 mb-2">{ext.name}</h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6 line-clamp-2 leading-relaxed">
                {ext.description}
              </p>

              <div className="flex items-center justify-between pt-6 border-t border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-4 text-[11px] text-zinc-400 font-medium">
                  <div className="flex items-center gap-1">
                    <Download className="w-3 h-3" /> {ext.downloads}
                  </div>
                  <div className="flex items-center gap-1">
                    v{ext.version}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-500 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                  </button>
                  {ext.installed ? (
                    <button className="px-4 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 text-sm font-bold text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all">
                      Configure
                    </button>
                  ) : (
                    <button className="px-4 py-1.5 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-sm font-bold hover:opacity-90 transition-all flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 fill-current" /> Install
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
