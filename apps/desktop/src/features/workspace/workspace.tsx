import React, { useState } from 'react';
import { WorkspaceItem, HistoryItem } from '../types';
import { LayoutGrid, List, FolderOpen, Plus, MoreVertical, Trash2, Pencil, ChevronLeft, MessageSquare, Search, Pin, ChevronRight } from 'lucide-react';

interface WorkspaceProps {
  workspaces: WorkspaceItem[];
  history: HistoryItem[];
  onSelectWorkspace: (id: string) => void;
  onCreateWorkspace: () => void;
  onRenameWorkspace: (id: string, newName: string) => void;
  onDeleteWorkspace: (id: string) => void;
  onSelectChat: (id: string) => void;
  onRenameChat: (id: string, newTitle: string) => void;
  onDeleteChat: (id: string) => void;
  onPinChat: (id: string) => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({
  workspaces,
  history,
  onSelectWorkspace,
  onCreateWorkspace,
  onRenameWorkspace,
  onDeleteWorkspace,
  onSelectChat,
  onRenameChat,
  onDeleteChat,
  onPinChat
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [openedWorkspaceId, setOpenedWorkspaceId] = useState<string | null>(null);

  const [chatSearchQuery, setChatSearchQuery] = useState('');
  const [chatMenuOpenId, setChatMenuOpenId] = useState<string | null>(null);
  const [chatEditingId, setChatEditingId] = useState<string | null>(null);
  const [chatEditTitle, setChatEditTitle] = useState('');

  const handleRenameStart = (workspace: WorkspaceItem) => {
    setEditingId(workspace.id);
    setEditName(workspace.name);
    setMenuOpenId(null);
  };

  const handleRenameSave = () => {
    if (editingId && editName.trim()) {
      onRenameWorkspace(editingId, editName.trim());
    }
    setEditingId(null);
  };

  const handleChatRenameStart = (chat: HistoryItem) => {
    setChatEditingId(chat.id);
    setChatEditTitle(chat.title);
    setChatMenuOpenId(null);
  };

  const handleChatRenameSave = () => {
    if (chatEditingId && chatEditTitle.trim()) {
      onRenameChat(chatEditingId, chatEditTitle.trim());
    }
    setChatEditingId(null);
  };

  const getSessionCount = (workspaceId: string) => {
    return history.filter(h => h.workspaceId === workspaceId).length;
  };

  if (openedWorkspaceId) {
    const workspace = workspaces.find(w => w.id === openedWorkspaceId);
    const sessions = history.filter(h => h.workspaceId === openedWorkspaceId);
    const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(chatSearchQuery.toLowerCase()));

    return (
      <div className="flex flex-col h-full bg-white dark:bg-[#1a1a1a] animate-fade-in">
        <div className="flex-shrink-0 flex items-center justify-between px-6 py-5 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-10 bg-white dark:bg-[#1a1a1a]">
          <div className="flex items-center gap-2 text-sm font-medium">
            <button 
              onClick={() => setOpenedWorkspaceId(null)}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors flex items-center gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Workspaces
            </button>
            <span className="text-zinc-300 dark:text-zinc-700">/</span>
            <span className="text-zinc-900 dark:text-zinc-100">{workspace?.name}</span>
          </div>
          <button 
            onClick={() => {
              onSelectWorkspace(openedWorkspaceId);
            }}
            className="flex items-center gap-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Chat in Workspace
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
          <div className="mb-6 relative max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Search chats..."
              value={chatSearchQuery}
              onChange={e => setChatSearchQuery(e.target.value)}
              className="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg pl-9 pr-4 py-2 text-sm outline-none focus:border-primary/50 transition-colors text-zinc-900 dark:text-zinc-100"
            />
          </div>

          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500 dark:text-zinc-400">
              <MessageSquare className="w-12 h-12 mb-4 opacity-20" />
              <p>No chat sessions in this workspace.</p>
              <button 
                onClick={() => onSelectWorkspace(openedWorkspaceId)}
                className="mt-4 text-primary hover:underline text-sm font-medium"
              >
                Start a new chat
              </button>
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500 dark:text-zinc-400">
              <Search className="w-12 h-12 mb-4 opacity-20" />
              <p>No chats found matching "{chatSearchQuery}".</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider border-b border-zinc-100 dark:border-zinc-800 mb-2">
                  <div className="col-span-6">Name</div>
                  <div className="col-span-3">Updated</div>
                  <div className="col-span-3 text-right">Actions</div>
              </div>

              <div className="space-y-1">
                  {filteredSessions.map(session => (
                      <div key={session.id} className="grid grid-cols-12 gap-4 items-center p-3 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-900/50 group transition-colors">
                          <div className="col-span-6 flex items-center gap-3 overflow-hidden">
                              <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                  <MessageSquare className="w-4 h-4" />
                              </div>
                              {chatEditingId === session.id ? (
                                  <input 
                                      value={chatEditTitle} 
                                      onChange={(e) => setChatEditTitle(e.target.value)}
                                      onBlur={handleChatRenameSave}
                                      onKeyDown={(e) => e.key === 'Enter' && handleChatRenameSave()}
                                      className="w-full bg-white dark:bg-zinc-800 border border-primary rounded px-2 py-1 text-sm"
                                      autoFocus
                                  />
                              ) : (
                                  <div className="flex items-center gap-2 truncate">
                                      <span 
                                          onClick={() => onSelectChat(session.id)}
                                          className="font-medium text-zinc-700 dark:text-zinc-200 truncate cursor-pointer hover:underline"
                                      >
                                          {session.title}
                                      </span>
                                      {session.pinned && <Pin className="w-3 h-3 text-zinc-400 fill-zinc-400 flex-shrink-0" />}
                                  </div>
                              )}
                          </div>
                          <div className="col-span-3 text-sm text-zinc-500">
                              {new Date(session.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                          </div>
                          <div className="col-span-3 flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => onPinChat(session.id)} className="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100" title={session.pinned ? "Unpin" : "Pin"}>
                                  <Pin className={`w-4 h-4 ${session.pinned ? 'fill-current' : ''}`} />
                              </button>
                              <button onClick={() => handleChatRenameStart(session)} className="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100" title="Rename">
                                  <Pencil className="w-4 h-4" />
                              </button>
                              <button onClick={() => onDeleteChat(session.id)} className="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded text-zinc-500 hover:text-red-600" title="Delete">
                                  <Trash2 className="w-4 h-4" />
                              </button>
                          </div>
                      </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#1a1a1a] animate-fade-in">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-5 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-10 bg-white dark:bg-[#1a1a1a]">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Workspaces</h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Manage your projects and chat sessions</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-zinc-100 dark:bg-zinc-800/50 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white dark:bg-zinc-700 shadow-sm text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white dark:bg-zinc-700 shadow-sm text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
          <button 
            onClick={onCreateWorkspace}
            className="flex items-center gap-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        {workspaces.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-500 dark:text-zinc-400">
            <FolderOpen className="w-12 h-12 mb-4 opacity-20" />
            <p>No workspaces found.</p>
            <button 
              onClick={onCreateWorkspace}
              className="mt-4 text-primary hover:underline text-sm font-medium"
            >
              Create your first workspace
            </button>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {workspaces.map(ws => (
              <div 
                key={ws.id} 
                className="group relative bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => setOpenedWorkspaceId(ws.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2 bg-white dark:bg-zinc-800 rounded-lg shadow-sm">
                    <FolderOpen className="w-5 h-5 text-zinc-700 dark:text-zinc-300" />
                  </div>
                  <div className="relative" onClick={e => e.stopPropagation()}>
                    <button 
                      onClick={() => setMenuOpenId(menuOpenId === ws.id ? null : ws.id)}
                      className="p-1 rounded-md text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>
                    {menuOpenId === ws.id && (
                      <div className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl z-20 py-1">
                        <button 
                          onClick={() => handleRenameStart(ws)}
                          className="w-full text-left px-3 py-1.5 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-700 flex items-center gap-2 text-zinc-700 dark:text-zinc-300"
                        >
                          <Pencil className="w-3.5 h-3.5" /> Rename
                        </button>
                        <button 
                          onClick={() => { onDeleteWorkspace(ws.id); setMenuOpenId(null); }}
                          className="w-full text-left px-3 py-1.5 text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 flex items-center gap-2"
                        >
                          <Trash2 className="w-3.5 h-3.5" /> Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                {editingId === ws.id ? (
                  <input
                    autoFocus
                    value={editName}
                    onChange={e => setEditName(e.target.value)}
                    onBlur={handleRenameSave}
                    onKeyDown={e => e.key === 'Enter' && handleRenameSave()}
                    onClick={e => e.stopPropagation()}
                    className="w-full bg-white dark:bg-zinc-800 border border-primary rounded px-2 py-1 text-sm outline-none mb-1 text-zinc-900 dark:text-zinc-100"
                  />
                ) : (
                  <h3 className="font-medium text-zinc-900 dark:text-zinc-100 truncate mb-1">{ws.name}</h3>
                )}
                <p className="text-xs text-zinc-500 dark:text-zinc-400">{getSessionCount(ws.id)} sessions</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 dark:bg-zinc-800/50 text-zinc-500 dark:text-zinc-400 border-b border-zinc-200 dark:border-zinc-800">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Sessions</th>
                  <th className="px-4 py-3 font-medium">Last Modified</th>
                  <th className="px-4 py-3 font-medium w-16"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {workspaces.map(ws => (
                  <tr 
                    key={ws.id} 
                    className="hover:bg-zinc-100/50 dark:hover:bg-zinc-800/30 transition-colors cursor-pointer group"
                    onClick={() => setOpenedWorkspaceId(ws.id)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <FolderOpen className="w-4 h-4 text-zinc-400" />
                        {editingId === ws.id ? (
                          <input
                            autoFocus
                            value={editName}
                            onChange={e => setEditName(e.target.value)}
                            onBlur={handleRenameSave}
                            onKeyDown={e => e.key === 'Enter' && handleRenameSave()}
                            onClick={e => e.stopPropagation()}
                            className="bg-white dark:bg-zinc-800 border border-primary rounded px-2 py-1 text-sm outline-none text-zinc-900 dark:text-zinc-100"
                          />
                        ) : (
                          <span className="font-medium text-zinc-900 dark:text-zinc-100">{ws.name}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-zinc-500 dark:text-zinc-400">{getSessionCount(ws.id)}</td>
                    <td className="px-4 py-3 text-zinc-500 dark:text-zinc-400">{new Date(ws.updatedAt).toLocaleDateString()}</td>
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      <div className="relative flex justify-end">
                        <button 
                          onClick={() => setMenuOpenId(menuOpenId === ws.id ? null : ws.id)}
                          className="p-1 rounded-md text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        {menuOpenId === ws.id && (
                          <div className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl z-20 py-1">
                            <button 
                              onClick={() => handleRenameStart(ws)}
                              className="w-full text-left px-3 py-1.5 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-700 flex items-center gap-2 text-zinc-700 dark:text-zinc-300"
                            >
                              <Pencil className="w-3.5 h-3.5" /> Rename
                            </button>
                            <button 
                              onClick={() => { onDeleteWorkspace(ws.id); setMenuOpenId(null); }}
                              className="w-full text-left px-3 py-1.5 text-sm hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 flex items-center gap-2"
                            >
                              <Trash2 className="w-3.5 h-3.5" /> Delete
                            </button>
                          </div>
                        )}
                      </div>
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
};