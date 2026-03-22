// ── Root Application Component ─────────────────────────

import { useEngineStore } from './stores/engine.store';
import { AppShell } from './components/app-shell';
import { SplashScreen } from './components/splash-screen';
import { useEngine } from './hooks/use-engine';

export default function App() {
  // Initialize engine event subscription
  useEngine();

  const connectionStatus = useEngineStore((s) => s.connectionStatus);

  if (connectionStatus === 'starting') {
    return <SplashScreen />;
  }

  return <AppShell />;
}
