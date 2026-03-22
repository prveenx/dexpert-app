"use client";

import { useSession } from "@/lib/auth-client";

export default function SettingsPage() {
    const { data: session } = useSession();

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-300 max-w-2xl">
            <h2 className="text-2xl font-bold">Account Settings</h2>
            
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm flex flex-col gap-6">
                 <div>
                     <label className="text-sm font-medium block mb-2">Email</label>
                     <input 
                        type="text" 
                        disabled 
                        value={session?.user.email || ''} 
                        className="w-full p-2 border rounded-md bg-zinc-50 dark:bg-zinc-950 opacity-70"
                     />
                 </div>
                 <div>
                     <label className="text-sm font-medium block mb-2">Name</label>
                     <input 
                        type="text" 
                        value={session?.user.name || ''} 
                        className="w-full p-2 border rounded-md bg-transparent"
                     />
                 </div>
                 <button className="self-end bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition">
                     Save changes
                 </button>
            </div>
            
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm flex flex-col gap-4 border-l-4 border-l-red-500">
                <h3 className="font-semibold text-red-600">Danger Zone</h3>
                <p className="text-sm text-zinc-500">Permanently delete your account and all associated data.</p>
                <button className="self-start bg-red-100 text-red-700 px-4 py-2 rounded-md hover:bg-red-200 transition text-sm font-medium mt-2">
                    Delete Account
                </button>
            </div>
        </div>
    );
}
