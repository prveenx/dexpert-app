"use client";

import { useState } from "react";
import { signIn, signUp } from "@/lib/auth-client";
import { useSearchParams } from "next/navigation";

export function AuthForm({ type }: { type: "login" | "signup" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const searchParams = useSearchParams();
  const platform = searchParams.get("platform");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (type === "signup") {
        await signUp.email({
          email,
          password,
          name,
          fetchOptions: {
            onResponse: (ctx) => {
              if (ctx.response.ok) {
                 // handle signup success
                 if (platform === "desktop") {
                    // DesktopRedirect should handle it
                 } else {
                    window.location.href = "/dashboard";
                 }
              }
            },
            onError: (ctx) => {
              setError(ctx.error.message || "An error occurred during signup");
            }
          }
        });
      } else {
        await signIn.email({
          email,
          password,
          fetchOptions: {
            onResponse: (ctx) => {
              if (ctx.response.ok) {
                if (platform === "desktop") {
                  // desktop redirect
                } else {
                  window.location.href = "/dashboard";
                }
              }
            },
            onError: (ctx) => {
              setError(ctx.error.message || "Invalid email or password");
            }
          }
        });
      }
    } catch (err: any) {
      setError(err?.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
      {type === "signup" && (
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">Name</label>
          <input
            type="text"
            required
            className="p-2 border rounded-md bg-transparent"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="John Doe"
          />
        </div>
      )}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium">Email</label>
        <input
          type="email"
          required
          className="p-2 border rounded-md bg-transparent"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email@example.com"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium">Password</label>
        <input
          type="password"
          required
          className="p-2 border rounded-md bg-transparent"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>

      {error && <div className="text-red-500 text-sm mt-2">{error}</div>}

      <button
        type="submit"
        disabled={loading}
        className="mt-4 bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {loading ? "Please wait..." : type === "login" ? "Log In" : "Sign Up"}
      </button>
    </form>
  );
}
