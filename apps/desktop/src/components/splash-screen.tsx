// ── Splash Screen ──────────────────────────────────────

export function SplashScreen() {
  return (
    <div className="flex h-screen flex-col items-center justify-center bg-gray-950">
      <div className="mb-8 flex items-center gap-3">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-dexpert-500 to-dexpert-700 flex items-center justify-center">
          <span className="text-2xl font-bold text-white">D</span>
        </div>
        <h1 className="text-3xl font-bold text-white">Dexpert</h1>
      </div>

      <div className="flex flex-col items-center gap-4">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-dexpert-500 border-t-transparent" />
        <p className="text-sm text-gray-400">Starting engine...</p>
      </div>

      <p className="mt-16 text-xs text-gray-600">
        Multi-Agent System • v0.1.0
      </p>
    </div>
  );
}
