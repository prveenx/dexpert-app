// ── App Shell (v2) ──────────────────────────────────
// Main IDE layout: TitleBar + Sidebar + Chat (Center) +
// Dynamic Workspace Panel (Right).
// ───────────────────────────────────────────────────────

import React, { useState, useCallback } from 'react';
import { TitleBar } from './title-bar';
import { Sidebar } from '../features/sidebar/sidebar';
import { ChatView } from '../features/chat/chat-view';
import { EngineStatusBanner } from './engine-status-banner';
import { useEngineHealth } from '../hooks/use-engine-health';
import { useSessionStore } from '../stores/session.store';
import { useWorkspaceStore } from '../stores/workspace.store';
import Workspace from '../features/workspace';
import { ExtensionsView } from '../features/extensions/extensions-view';
import { SettingsView } from '../features/settings/settings-view';

export function AppShell() {
  const status = useEngineHealth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState<'chat' | 'workspace' | 'extensions' | 'settings'>('chat');
  
  // Workspace integration
  const isWorkspaceOpen = useWorkspaceStore(s => s.isOpen);

  // Session Store
  const sessions = useSessionStore((s) => s.sessions);
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const setActive = useSessionStore((s) => s.setActive);
  const renameSession = useSessionStore((s) => s.renameSession);
  const deleteSession = useSessionStore((s) => s.deleteSession);
  const togglePinSession = useSessionStore((s) => s.togglePinSession);

  const handleNewTask = useCallback(() => {
    const newId = crypto.randomUUID();
    setActive(newId);
    setCurrentView('chat');
  }, [setActive]);

  // View Switcher Helper
  const renderView = () => {
    switch (currentView) {
      case 'chat':
        return <ChatView />;
      case 'extensions':
        return <ExtensionsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <ChatView />;
    }
  };

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      <TitleBar />
      
      {(status === 'degraded' || status === 'offline') && <EngineStatusBanner />}

      <div className="flex flex-1 overflow-hidden relative">
        {/* Left: Navigation Sidebar */}
        <Sidebar 
          isOpen={isSidebarOpen}
          currentView={currentView}
          setView={setCurrentView}
          sessions={sessions}
          activeSessionId={currentSessionId}
          onNewTask={handleNewTask}
          onSelectSession={(id) => {
            setActive(id);
            setCurrentView('chat');
          }}
          onRenameSession={renameSession}
          onDeleteSession={deleteSession}
          onTogglePinSession={togglePinSession}
          onToggleCollapse={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Center: Dynamic Primary Content View (Chat, Extensions, etc) */}
        <main className={`flex-1 flex flex-col min-w-0 bg-white dark:bg-zinc-950 relative z-10 shadow-2xl transition-all duration-300 ${isWorkspaceOpen && currentView === 'chat' ? 'mr-0' : ''}`}>
          {renderView()}
        </main>

        {/* Right: Dynamic IDE Workspace Panel ( slides in over chat ) */}
        {currentView === 'chat' && <Workspace />}
      </div>
    </div>
  );
}
