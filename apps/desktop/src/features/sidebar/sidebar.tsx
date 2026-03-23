// ── Sidebar ────────────────────────────────────────────
// Left navigation panel for sessions and settings.
// ───────────────────────────────────────────────────────

import React, { useState, useRef, useEffect } from 'react';
import type { Session } from '@dexpert/types';
import {
  PanelLeftClose,
  MoreHorizontal,
  Trash2,
  Pencil,
  Settings,
  LogOut,
  Blocks,
  LayoutGrid,
  Bot,
  Pin,
  PinOff
} from 'lucide-react';

interface SidebarItemProps {
  session: Session;
  isActive: boolean;
  onClick: () => void;
  onRename: (id: string, newTitle: string) => void;
  onDelete: (id: string) => void;
  onTogglePin: (id: string) => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  session,
  isActive,
  onClick,
  onRename,
  onDelete,
  onTogglePin,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isEditing && inputRef.current) inputRef.current.focus();
  }, [isEditing]);

  const handleSaveRename = () => {
    if (editTitle.trim() && editTitle !== session.title) {
      onRename(session.id, editTitle);
    }
    setIsEditing(false);
    setIsMenuOpen(false);
  };

  return (
    <div
      className={`group relative flex items-center justify-between px-3 py-2 mx-2 rounded-xl cursor-pointer text-sm transition-all duration-200 ${
        isActive
          ? 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20'
          : 'hover:bg-zinc-100 dark:hover:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400 border border-transparent'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className="relative shrink-0">
          <Bot className={`w-4 h-4 ${isActive ? 'text-violet-500' : 'text-zinc-400'}`} />
          {session.pinned && (
            <Pin className="w-2 h-2 text-violet-500 absolute -top-1 -right-1 fill-violet-500" />
          )}
        </div>
        {isEditing ? (
          <input
            ref={inputRef}
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleSaveRename}
            onKeyDown={(e) => e.key === 'Enter' && handleSaveRename()}
            className="w-full bg-transparent outline-none text-sm font-medium"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="truncate font-medium">{session.title || 'Untitled Session'}</span>
        )}
      </div>

      <div className="relative" ref={menuRef}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsMenuOpen(!isMenuOpen);
          }}
          className={`p-1 rounded-lg text-zinc-500 opacity-0 group-hover:opacity-100 ${
            isMenuOpen ? 'opacity-100 bg-zinc-100 dark:bg-zinc-800' : ''
          } hover:text-zinc-900 dark:hover:text-zinc-100 transition-all`}
        >
          <MoreHorizontal className="w-4 h-4" />
        </button>

        {isMenuOpen && (
          <div className="absolute right-0 top-8 w-40 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-xl z-50 py-1.5 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
                setIsMenuOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2.5 text-zinc-700 dark:text-zinc-300"
            >
              <Pencil className="w-3.5 h-3.5" /> Rename
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin(session.id);
                setIsMenuOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-2.5 text-zinc-700 dark:text-zinc-300"
            >
              {session.pinned ? (
                <>
                  <PinOff className="w-3.5 h-3.5" /> Unpin
                </>
              ) : (
                <>
                  <Pin className="w-3.5 h-3.5" /> Pin
                </>
              )}
            </button>
            <div className="h-px bg-zinc-100 dark:bg-zinc-800 my-1" />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(session.id);
                setIsMenuOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-xs hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 flex items-center gap-2.5"
            >
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

interface SidebarProps {
  isOpen: boolean;
  currentView: 'chat' | 'workspace' | 'extensions' | 'settings';
  setView: (view: 'chat' | 'workspace' | 'extensions' | 'settings') => void;
  sessions: Session[];
  activeSessionId: string | null;
  onNewTask: () => void;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  onDeleteSession: (id: string) => void;
  onTogglePinSession: (id: string) => void;
  onToggleCollapse: () => void;
}

const NavItem: React.FC<{
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  onClick: () => void;
  isOpen: boolean;
}> = ({ icon, label, isActive, onClick, isOpen }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-3 w-[calc(100%-16px)] mx-2 p-2.5 rounded-xl transition-all duration-200 ${
      isActive
        ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 shadow-sm'
        : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50'
    } ${!isOpen ? 'justify-center' : ''}`}
    title={!isOpen ? label : undefined}
  >
    <div className={`${isActive ? 'scale-110' : ''} transition-transform`}>
      {icon}
    </div>
    {isOpen && <span className="text-sm font-semibold">{label}</span>}
  </button>
);

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  currentView,
  setView,
  sessions,
  activeSessionId,
  onNewTask,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
  onTogglePinSession,
  onToggleCollapse,
}) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div
      className={`relative flex-shrink-0 flex flex-col h-full bg-zinc-50 dark:bg-[#09090b] border-r border-zinc-200 dark:border-zinc-800 transition-all duration-300 ease-in-out ${
        isOpen ? 'w-[280px]' : 'w-[76px]'
      }`}
    >
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        {isOpen && (
          <div className="flex items-center gap-2.5 px-2">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <span className="font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight text-lg">Dexpert</span>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className={`p-2 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded-xl text-zinc-500 transition-colors ${
            !isOpen ? 'mx-auto' : ''
          }`}
        >
          <PanelLeftClose className={`w-5 h-5 ${!isOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* New Task Button */}
      <div className="px-4 mb-6">
        <button
          onClick={onNewTask}
          className={`flex items-center gap-3 w-full p-3 rounded-xl bg-violet-600 hover:bg-violet-700 text-white transition-all shadow-md shadow-violet-500/10 ${
            !isOpen ? 'justify-center' : ''
          }`}
        >
          <div className="w-5 h-5 flex items-center justify-center font-bold text-xl leading-none">+</div>
          {isOpen && <span className="text-sm font-bold">New Mission</span>}
        </button>
      </div>

      {/* Scrollable Area */}
      <div className="flex-1 overflow-y-auto space-y-8 pt-2 custom-scrollbar pb-4">
        {/* Main Navigation */}
        <div className="space-y-1">
          {isOpen && (
            <div className="px-6 py-2 text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] mb-1">
              Menu
            </div>
          )}
          <NavItem
            icon={<Bot className="w-5 h-5" />}
            label="Chat"
            isActive={currentView === 'chat'}
            onClick={() => setView('chat')}
            isOpen={isOpen}
          />
          <NavItem
            icon={<LayoutGrid className="w-5 h-5" />}
            label="Workspace"
            isActive={currentView === 'workspace'}
            onClick={() => setView('workspace')}
            isOpen={isOpen}
          />
          <NavItem
            icon={<Blocks className="w-5 h-5" />}
            label="Extensions"
            isActive={currentView === 'extensions'}
            onClick={() => setView('extensions')}
            isOpen={isOpen}
          />
        </div>

        {/* Recent Sessions */}
        <div className="space-y-1">
          {isOpen && (
            <div className="px-6 py-2 text-[10px] font-bold text-zinc-400 uppercase tracking-[0.2em] mb-1">
              Recent Sessions
            </div>
          )}
          <div className="space-y-0.5">
            {[...sessions]
              .sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0))
              .map((session) => (
                <SidebarItem
                  key={session.id}
                  session={session}
                  isActive={activeSessionId === session.id && currentView === 'chat'}
                  onClick={() => onSelectSession(session.id)}
                  onRename={onRenameSession}
                  onDelete={onDeleteSession}
                  onTogglePin={onTogglePinSession}
                />
              ))}
            {sessions.length === 0 && isOpen && (
              <div className="px-6 py-4 text-xs text-zinc-400 italic">No missions yet</div>
            )}
            {!isOpen && sessions.length > 0 && (
              <div className="flex flex-col items-center gap-3 py-2 opacity-50">
                <div className="w-8 h-px bg-zinc-200 dark:bg-zinc-800" />
                <Bot className="w-5 h-5 text-zinc-400" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer / Profile */}
      <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-black/20" ref={profileRef}>
        {isProfileOpen && isOpen && (
          <div className="absolute bottom-[85px] left-4 right-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl p-1.5 z-50 animate-in slide-in-from-bottom-2 duration-200">
            <button 
              onClick={() => { setView('settings'); setIsProfileOpen(false); }}
              className={`w-full text-left px-3 py-2.5 text-sm rounded-xl hover:bg-zinc-50 dark:hover:bg-zinc-800 flex items-center gap-3 ${currentView === 'settings' ? 'text-violet-600' : 'text-zinc-600 dark:text-zinc-300'}`}
            >
              <Settings className="w-4 h-4" /> Settings
            </button>
            <div className="h-px bg-zinc-100 dark:bg-zinc-800 my-1.5" />
            <button className="w-full text-left px-3 py-2.5 text-sm rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 flex items-center gap-3">
              <LogOut className="w-4 h-4" /> Log out
            </button>
          </div>
        )}

        <button
          onClick={() => (isOpen ? setIsProfileOpen(!isProfileOpen) : onToggleCollapse())}
          className={`flex items-center gap-3 w-full p-2 rounded-xl hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors ${
            !isOpen ? 'justify-center' : ''
          }`}
        >
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-[10px] font-bold shrink-0 shadow-md">
            USER
          </div>
          {isOpen && (
            <div className="flex-1 min-w-0 text-left">
              <p className="text-sm font-bold text-zinc-800 dark:text-zinc-200 truncate">Dexpert User</p>
              <p className="text-[10px] text-zinc-400 font-medium">Free Tier</p>
            </div>
          )}
        </button>
      </div>
    </div>
  );
};