// ── Engine Port ────────────────────────────────────────
// Finds a free port for the engine (default 48765, fallback +1..+10)
// ───────────────────────────────────────────────────────

import { createServer } from 'net';

export function findFreePort(startPort: number = 48765): Promise<number> {
  return new Promise((resolve, reject) => {
    let currentPort = startPort;
    const maxAttempts = 10;

    function tryPort(port: number, attempt: number): void {
      if (attempt >= maxAttempts) {
        reject(new Error(`Could not find a free port after ${maxAttempts} attempts`));
        return;
      }

      const server = createServer();
      server.listen(port, '127.0.0.1', () => {
        server.close(() => resolve(port));
      });
      server.on('error', () => {
        tryPort(port + 1, attempt + 1);
      });
    }

    tryPort(currentPort, 0);
  });
}
