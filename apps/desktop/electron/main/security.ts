// ── Security Hardening ─────────────────────────────────

import { app, session } from 'electron';

export function setupSecurity(): void {
  // Disable navigation to unknown origins
  app.on('web-contents-created', (_event, contents) => {
    contents.on('will-navigate', (event, url) => {
      const allowedOrigins = ['http://localhost', 'https://localhost'];
      const isAllowed = allowedOrigins.some((origin) => url.startsWith(origin));
      if (!isAllowed) {
        event.preventDefault();
      }
    });
  });

  // Set Content Security Policy
  app.on('ready', () => {
    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': [
            "default-src 'self'; " +
            "script-src 'self'; " +
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
            "font-src 'self' https://fonts.gstatic.com; " +
            "img-src 'self' data: blob:; " +
            "connect-src 'self' ws://127.0.0.1:* http://127.0.0.1:*;",
          ],
        },
      });
    });
  });
}
