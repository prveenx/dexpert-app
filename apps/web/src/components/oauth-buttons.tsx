"use client";

import { signIn } from "@/lib/auth-client";
import { Github, Mail } from "lucide-react"; // Assume lucide-react is installed

export function OAuthButtons() {
  const handleGoogle = async () => {
    await signIn.social({
        provider: "google",
        callbackURL: "/dashboard" // Will be intercepted if desktop
    });
  };

  const handleGithub = async () => {
    await signIn.social({
        provider: "github",
        callbackURL: "/dashboard"
    });
  };

  return (
    <div className="flex flex-col gap-3 w-full">
      <button
        onClick={handleGithub}
        className="flex items-center justify-center gap-2 border p-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
      >
        <Github size={18} />
        Continue with GitHub
      </button>
      <button
        onClick={handleGoogle}
        className="flex items-center justify-center gap-2 border p-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
      >
        <Mail size={18} />
        Continue with Google
      </button>
    </div>
  );
}
