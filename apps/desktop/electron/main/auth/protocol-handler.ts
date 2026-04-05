import { app, BrowserWindow } from 'electron';
import { TokenStore } from './token-store';

export function handleDeepLink(url: string, window: BrowserWindow | null) {
  try {
    const parsedUrl = new URL(url);
    if (parsedUrl.host === 'token') {
      const jwt = parsedUrl.searchParams.get('jwt');
      if (jwt) {
        // Save the JWT
        TokenStore.save(jwt);
        
        // Notify the window
        if (window && !window.isDestroyed()) {
          window.webContents.send('auth:success');
          app.emit('auth-success' as any);
        }
      }
    }
  } catch (e) {
    console.error('Invalid deep link:', url, e);
  }
}
