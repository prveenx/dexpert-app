"use client";

import { useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { OAuthButtons } from "@/components/oauth-buttons";
import DesktopRedirect from "@/components/desktop-redirect";

function LoginContent() {
  const searchParams = useSearchParams();
  const platform = searchParams.get("platform");
  const isDesktop = platform === "desktop";

  useEffect(() => {
    if (isDesktop) {
      document.body.style.overflow = "hidden";
      document.body.classList.add("platform-desktop");
    }
  }, [isDesktop]);

  return (
    <div className={`flex flex-col w-full animate-in fade-in zoom-in duration-300 ${isDesktop ? 'max-w-md mx-auto py-12' : ''}`}>
      {!isDesktop && (
        <>
          <h2 className="text-xl font-bold mb-6 text-center">Welcome back</h2>
          <OAuthButtons />
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t dark:border-zinc-700"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white dark:bg-zinc-900 px-2 text-zinc-500">Or continue with</span>
            </div>
          </div>
        </>
      )}

      {isDesktop && (
        <div className="text-center mb-8">
           <div className="w-20 h-20 bg-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl">
             <span className="text-white text-4xl font-bold">D</span>
           </div>
           <h1 className="text-3xl font-bold tracking-tighter">Dexpert</h1>
           <p className="text-zinc-500 text-sm mt-1">Desktop Authentication Gateway</p>
        </div>
      )}

      <AuthForm type="login" />
      <DesktopRedirect />
      
      {!isDesktop && (
        <div className="mt-6 text-center text-sm text-zinc-500">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-blue-600 hover:underline">
            Sign up
          </Link>
        </div>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-32 text-zinc-400">Loading auth...</div>}>
      <LoginContent />
    </Suspense>
  );
}
