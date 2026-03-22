// ── App Shell ──────────────────────────────────────────
// Main authenticated layout: TitleBar + Sidebar + Chat + AgentsPanel
// ───────────────────────────────────────────────────────

import React, { useState, useCallback } from 'react';
import { TitleBar } from './title-bar';
import { Sidebar } from '../features/sidebar';
import { ChatView } from '../features/chat';
import { AgentsPanel } from '../features/agents-panel';
import { EngineStatusBanner } from './engine-status-banner';
import { useEngineHealth } from '../hooks/use-engine-health';
import { useSessionStore } from '../stores/session.store';

export function AppShell() {
  const status = useEngineHealth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // Session Store
  const sessions = useSessionStore((s) => s.sessions);
  const currentSessionId = useSessionStore((s) => s.currentSessionId);
  const setActive = useSessionStore((s) => s.setActive);
  const renameSession = useSessionStore((s) => s.renameSession);
  const deleteSession = useSessionStore((s) => s.deleteSession);

  const handleNewTask = useCallback(() => {
    // In a real app, this would hit the API and then setActive
    const newId = crypto.randomUUID();
    // This is just a UI-only demo for now, usually the engine creates sessions
    setActive(newId);
  }, [setActive]);

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      <TitleBar />
      
      {(status === 'degraded' || status === 'offline') && <EngineStatusBanner />}

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar 
          isOpen={isSidebarOpen}
          sessions={sessions}
          activeSessionId={currentSessionId}
          onNewTask={handleNewTask}
          onSelectSession={setActive}
          onRenameSession={renameSession}
          onDeleteSession={deleteSession}
          onToggleCollapse={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Chat (main center area) */}
        <main className="flex-1 flex flex-col min-w-0 bg-white dark:bg-zinc-950 relative z-10 shadow-2xl">
          <ChatView />
        </main>

        {/* Agents Panel (right-side activity monitor) */}
        <aside className="w-80 flex-shrink-0 border-l border-zinc-200 dark:border-zinc-800 hidden lg:block">
          <AgentsPanel />
        </aside>
      </div>
    </div>
  );
}
