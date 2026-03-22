import Link from "next/link";
import { AuthForm } from "@/components/auth-form";

export default function MarketingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 items-center animate-in fade-in duration-500">
      <header className="w-full h-16 border-b flex items-center justify-between px-8 bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 shrink-0">
        <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center text-white font-bold text-sm">D</div>
            <span className="font-bold tracking-tight">Dexpert</span>
        </div>
        <nav className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium hover:text-blue-600 transition">Log In</Link>
            <Link href="/signup" className="text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 px-4 py-2 rounded-md hover:bg-zinc-800 dark:hover:bg-zinc-100 transition">Sign Up</Link>
        </nav>
      </header>
      
      <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl text-center">
        <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 bg-gradient-to-br from-zinc-900 to-zinc-500 bg-clip-text text-transparent dark:from-white dark:to-zinc-500">
          The Universal AI Platform
        </h1>
        <p className="text-xl text-zinc-500 max-w-2xl mb-10 leading-relaxed">
          Unleash the power of multi-agent workflows right from your desktop. Dexpert connects your tools, automates your routines, and extends your capabilities seamlessly.
        </p>
        <div className="flex flex-col gap-4 sm:flex-row mb-20 w-full sm:w-auto items-center justify-center">
             <Link href="/signup" className="text-lg font-medium bg-blue-600 text-white px-8 py-3 rounded-full hover:bg-blue-700 transition w-full sm:w-auto text-center shadow-lg shadow-blue-500/20">
                Get Started
            </Link>
             <Link href="#features" className="text-lg font-medium bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-white px-8 py-3 rounded-full hover:bg-zinc-50 dark:hover:bg-zinc-800 transition w-full sm:w-auto text-center">
                Learn More
            </Link>
        </div>
      </main>
    </div>
  );
}
