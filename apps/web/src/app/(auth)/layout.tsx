import { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-zinc-50 dark:bg-zinc-950">
      <div className="w-full max-w-md bg-white dark:bg-zinc-900 border dark:border-zinc-800 rounded-xl shadow-sm overflow-hidden p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl mb-4">
            D
          </div>
          <h1 className="text-2xl font-bold">Dexpert</h1>
          <p className="text-zinc-500 text-sm mt-1">AI Multi-Agent Platform</p>
        </div>
        {children}
      </div>
    </div>
  );
}
