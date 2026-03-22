"use client";

import { useSession, signOut } from "@/lib/auth-client";
import Link from "next/link";
import { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { data: session, isPending } = useSession();

  if (isPending) return <div className="p-8">Loading dashboard...</div>;
  if (!session) {
      if (typeof window !== "undefined") window.location.href = "/login";
      return null;
  }

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 flex flex-col">
          <div className="h-16 flex items-center px-6 border-b border-zinc-200 dark:border-zinc-800 shrink-0">
             <span className="font-bold tracking-tight">Dexpert Dashboard</span>
          </div>
          <nav className="flex-1 p-4 flex flex-col gap-2">
              <Link href="/dashboard" className="px-4 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition text-sm font-medium">Home</Link>
              <Link href="/settings" className="px-4 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition text-sm font-medium">Settings</Link>
          </nav>
          <div className="p-4 border-t border-zinc-200 dark:border-zinc-800">
             <div className="flex items-center gap-3 mb-4">
                 <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs uppercase overflow-hidden">
                     {session.user.image ? <img src={session.user.image} alt="" className="w-full h-full object-cover"/> : session.user.name?.[0] || 'U'}
                 </div>
                 <div className="flex flex-col flex-1 min-w-0">
                     <span className="text-sm font-medium truncate">{session.user.name}</span>
                     <span className="text-xs text-zinc-500 truncate">{session.user.email}</span>
                 </div>
             </div>
             <button onClick={() => signOut()} className="w-full py-2 px-4 rounded-md border text-sm font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition text-red-600 dark:text-red-400 border-red-200 dark:border-red-900/30">
                 Sign Out
             </button>
          </div>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto flex flex-col">
          <header className="h-16 border-b bg-white/50 backdrop-blur-sm dark:bg-zinc-900/50 border-zinc-200 dark:border-zinc-800 shrink-0 flex items-center px-8 z-10 sticky top-0">
             <h1 className="text-lg font-semibold">Admin Panel</h1>
          </header>
          <div className="p-8 flex-1">
             {children}
          </div>
      </main>
    </div>
  );
}
