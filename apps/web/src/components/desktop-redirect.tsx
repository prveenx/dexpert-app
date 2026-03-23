"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useSession } from "@/lib/auth-client";

export default function DesktopRedirect() {
  const searchParams = useSearchParams();
  const platform = searchParams.get("platform");
  const { data: session } = useSession();

  useEffect(() => {
    // If we have a session and the platform is desktop
    if (session && platform === "desktop") {
      // The electron app intercepts dexpert://token?jwt=...
      // but with better auth we might use the session token instead of JWT, or pass auth cookie equivalent. 
      // Better-Auth returns tokens or sets cookies. Wait, we may need to fetch custom token endpoint to get desktop JWT.
      // Let's call /api/desktop-token to get a signed JWT
      fetch("/api/desktop-token")
        .then(res => res.json())
        .then(async data => {
          if (data.token) {
            // Check if we are inside electron via the bridge
            const dexpert = (window as any).dexpert;
            if (dexpert?.auth?.setToken) {
              console.log("Directing token to Electron bridge...");
              await dexpert.auth.setToken(data.token);
              // The main process will handle window swap, but we can also trigger a local event
            } else {
              console.log("Using protocol redirect for auth...");
              window.location.href = `dexpert://token?jwt=${data.token}`;
            }
          }
        });
    }
  }, [session, platform]);

  if (session && platform === "desktop") {
    return (
      <div className="p-4 bg-green-500/10 text-green-500 rounded-md text-sm mt-4 text-center">
        Authentication successful! Redirecting to Dexpert Desktop App...
      </div>
    );
  }

  return null;
}
