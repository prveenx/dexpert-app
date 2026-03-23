import React, { useState } from 'react';
import { FolderOpen, Search, Plus, Filter, LayoutGrid, List, MoreVertical, FileText, Globe, Code, File as FileIcon } from 'lucide-react';

export function WorkspaceView() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const workspaces = [
    {
      id: 'ws-1',
      name: 'Project Alpha',
      description: 'Web development and system design notes.',
      updated: '2 hours ago',
      files: 12,
      color: 'bg-violet-600',
    },
    {
      id: 'ws-2',
      name: 'Personal Research',
      description: 'LLM agents and MCP experiments.',
      updated: 'Yesterday',
      files: 5,
      color: 'bg-indigo-600',
    },
    {
      id: 'ws-3',
      name: 'Dexpert Desktop App',
      description: 'System architecture and Electron integration.',
      updated: '3 days ago',
      files: 45,
      color: 'bg-blue-600',
    }
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-950 animate-in fade-in duration-500">
      <div className="flex-shrink-0 px-8 py-6 border-b border-zinc-200 dark:border-zinc-800 bg-white/10 backdrop-blur-3xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Workspaces</h1>
            <p className="text-zinc-500 text-sm mt-1">Organize your files, code, and agent memories.</p>
          </div>
          <button className="bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-5 py-2.5 rounded-xl text-sm font-extrabold shadow-xl hover:scale-105 transition-all flex items-center gap-2">
            <Plus className="w-4.5 h-4.5" /> Create Workspace
          </button>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 max-w-xl relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-zinc-400" />
            <input 
              type="text" 
              placeholder="Search all workspace documents..." 
              className="w-full pl-11 pr-4 py-3 bg-zinc-100 dark:bg-zinc-900 border border-transparent focus:border-violet-500/50 rounded-2xl text-sm transition-all outline-none"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <button className="p-3 bg-zinc-100 dark:bg-zinc-900 border border-transparent hover:border-zinc-200 dark:hover:border-zinc-800 rounded-2xl text-zinc-500 transition-all">
              <Filter className="w-5 h-5" />
            </button>
            <div className="w-px h-8 bg-zinc-200 dark:bg-zinc-800 mx-2" />
            <div className="flex p-1.5 bg-zinc-100 dark:bg-zinc-900 rounded-2xl border border-transparent">
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-xl transition-all ${viewMode === 'grid' ? 'bg-white dark:bg-zinc-800 text-violet-600 shadow-sm' : 'text-zinc-400 hover:text-zinc-600'}`}
              >
                <LayoutGrid className="w-4.5 h-4.5" />
              </button>
              <button 
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-xl transition-all ${viewMode === 'list' ? 'bg-white dark:bg-zinc-800 text-violet-600 shadow-sm' : 'text-zinc-400 hover:text-zinc-600'}`}
              >
                <List className="w-4.5 h-4.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8 bg-zinc-50/30 dark:bg-zinc-900/10 custom-scrollbar">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {workspaces.map(ws => (
              <div key={ws.id} className="group flex flex-col bg-white dark:bg-zinc-900 border border-zinc-200/50 dark:border-zinc-800/50 rounded-3xl p-6 hover:shadow-2xl hover:shadow-violet-500/10 hover:border-violet-500/20 transition-all duration-500 cursor-pointer">
                <div className="flex items-center justify-between mb-8">
                  <div className={`w-14 h-14 ${ws.color} rounded-2xl flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform duration-500`}>
                    <FolderOpen className="w-7 h-7" />
                  </div>
                  <button className="p-2.5 opacity-0 group-hover:opacity-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl text-zinc-400 transition-all">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
                
                <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-2 truncate">{ws.name}</h3>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-8 line-clamp-2 leading-relaxed">
                  {ws.description}
                </p>
                
                <div className="mt-auto flex items-center justify-between pt-6 border-t border-zinc-100 dark:border-zinc-800/50">
                  <div className="flex -space-x-2">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="w-8 h-8 rounded-full border-2 border-white dark:border-zinc-900 bg-zinc-200 dark:bg-zinc-800 flex items-center justify-center overflow-hidden">
                        {i === 1 ? <FileText className="w-4 h-4 text-blue-500" /> : i === 2 ? <Code className="w-4 h-4 text-emerald-500" /> : <Globe className="w-4 h-4 text-amber-500" />}
                      </div>
                    ))}
                    <div className="w-8 h-8 rounded-full border-2 border-white dark:border-zinc-900 bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-500">
                      +{ws.files - 3}
                    </div>
                  </div>
                  <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider">{ws.updated}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="max-w-6xl mx-auto bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl overflow-hidden shadow-sm">
             <table className="w-full text-left">
               <thead>
                 <tr className="border-b border-zinc-100 dark:border-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest px-6">
                    <th className="px-8 py-5">Name</th>
                    <th className="px-8 py-5">Activity</th>
                    <th className="px-8 py-5">Status</th>
                    <th className="px-8 py-5 text-right">Size</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/50">
                 {workspaces.map(ws => (
                   <tr key={ws.id} className="group hover:bg-zinc-50/50 dark:hover:bg-zinc-800/30 transition-all cursor-pointer">
                     <td className="px-8 py-5">
                       <div className="flex items-center gap-4">
                         <div className={`w-10 h-10 ${ws.color} rounded-xl flex items-center justify-center text-white group-hover:scale-110 transition-transform`}>
                           <FolderOpen className="w-5 h-5" />
                         </div>
                         <div>
                            <div className="text-sm font-bold text-zinc-900 dark:text-zinc-100">{ws.name}</div>
                            <div className="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">{ws.description}</div>
                         </div>
                       </div>
                     </td>
                     <td className="px-8 py-5">
                       <div className="flex flex-col gap-1.5">
                          <div className="w-32 h-1 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                             <div className="h-full bg-violet-600 rounded-full" style={{ width: '65%' }} />
                          </div>
                          <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-tighter">{ws.updated}</span>
                       </div>
                     </td>
                     <td className="px-8 py-5">
                       <span className="px-3 py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-full text-[10px] font-extrabold flex items-center gap-1.5 w-fit">
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Active
                       </span>
                     </td>
                     <td className="px-8 py-5 text-right">
                       <span className="text-sm font-bold text-zinc-500 dark:text-zinc-600">{ws.files} Files</span>
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table>
          </div>
        )}
      </div>
    </div>
  );
}
