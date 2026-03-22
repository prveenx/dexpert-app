import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { OAuthButtons } from "@/components/oauth-buttons";
import DesktopRedirect from "@/components/desktop-redirect";
import { Suspense } from "react";

export default function SignupPage() {
  return (
    <div className="flex flex-col w-full animate-in fade-in zoom-in duration-300">
      <h2 className="text-xl font-bold mb-6 text-center">Create an account</h2>
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
        <AuthForm type="signup" />
        <DesktopRedirect />
      </Suspense>
      <div className="mt-6 text-center text-sm text-zinc-500">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-600 hover:underline">
          Log in
        </Link>
      </div>
    </div>
  );
}
