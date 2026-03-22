"use client";

import { useSession } from "@/lib/auth-client";

export default function DashboardHome() {
    const { data: session } = useSession();

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-300">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                 <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm">
                     <h3 className="text-sm font-medium text-zinc-500 mb-2">Total Tasks</h3>
                     <p className="text-3xl font-bold">1,248</p>
                 </div>
                 <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm">
                     <h3 className="text-sm font-medium text-zinc-500 mb-2">Active Agents</h3>
                     <p className="text-3xl font-bold text-green-600">3</p>
                 </div>
                 <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm">
                     <h3 className="text-sm font-medium text-zinc-500 mb-2">API Usage</h3>
                     <p className="text-3xl font-bold">$12.40</p>
                     <p className="text-xs text-zinc-400 mt-2">Current month</p>
                 </div>
             </div>

             <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm flex-1">
                  <h3 className="text-lg font-semibold mb-4">Welcome back, {session?.user.name}</h3>
                  <p className="text-zinc-600 dark:text-zinc-400">
                      Manage your Dexpert account, billing, and settings here. For using the AI Agents, please continue to use the Desktop Application.
                  </p>
             </div>
        </div>
    );
}
