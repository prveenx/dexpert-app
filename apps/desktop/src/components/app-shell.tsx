// ── App Shell ──────────────────────────────────────────
// Main authenticated layout: TitleBar + Sidebar + Chat
// ───────────────────────────────────────────────────────

import React, { useState, useCallback } from 'react';
import { TitleBar } from './title-bar';
import { Sidebar } from '../features/sidebar/sidebar';
import { ChatView } from '../features/chat/chat-view';
import { EngineStatusBanner } from './engine-status-banner';
import { useEngineHealth } from '../hooks/use-engine-health';
import { useSessionStore } from '../stores/session.store';
import { WorkspaceView } from '../features/workspace/workspace-view';
import { ExtensionsView } from '../features/extensions/extensions-view';

export function AppShell() {
  const status = useEngineHealth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState<'chat' | 'workspace' | 'extensions' | 'settings'>('chat');
  
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
      case 'workspace':
        return <WorkspaceView />;
      case 'extensions':
        return <ExtensionsView />;
      case 'settings':
        return <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 bg-white dark:bg-zinc-950 p-8">
          <h2 className="text-2xl font-bold text-zinc-800 dark:text-zinc-200 mb-4">Settings</h2>
          <p className="max-w-md text-center">Configure your models, API keys, and personalization preferences here.</p>
        </div>;
      default:
        return <ChatView />;
    }
  };

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      <TitleBar />
      
      {(status === 'degraded' || status === 'offline') && <EngineStatusBanner />}

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
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

        {/* Dynamic View Area */}
        <main className="flex-1 flex flex-col min-w-0 bg-white dark:bg-zinc-950 relative z-10 shadow-2xl">
          {renderView()}
        </main>
      </div>
    </div>
  );
}
