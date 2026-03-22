import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { OAuthButtons } from "@/components/oauth-buttons";
import DesktopRedirect from "@/components/desktop-redirect";
import { Suspense } from "react";

export default function LoginPage() {
  return (
    <div className="flex flex-col w-full animate-in fade-in zoom-in duration-300">
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
      <Suspense fallback={null}>
        <AuthForm type="login" />
        <DesktopRedirect />
      </Suspense>
      <div className="mt-6 text-center text-sm text-zinc-500">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-blue-600 hover:underline">
          Sign up
        </Link>
      </div>
    </div>
  );
}
