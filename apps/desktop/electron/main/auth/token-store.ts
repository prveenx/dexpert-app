import { safeStorage, app } from 'electron';
import * as fs from 'fs';
import * as path from 'path';

const TOKEN_PATH = path.join(app.getPath('userData'), 'auth_token.enc');

export class TokenStore {
  static save(jwt: string): void {
    try {
      if (safeStorage.isEncryptionAvailable()) {
        const encrypted = safeStorage.encryptString(jwt);
        fs.writeFileSync(TOKEN_PATH, encrypted);
      } else {
        // Fallback for non-encrypted OSes or if safeStorage fails
        fs.writeFileSync(TOKEN_PATH, jwt, 'utf8');
      }
    } catch (e) {
      console.error('Failed to save token:', e);
    }
  }

  static get(): string | null {
    try {
      if (!fs.existsSync(TOKEN_PATH)) return null;
      const data = fs.readFileSync(TOKEN_PATH);
      if (safeStorage.isEncryptionAvailable()) {
        return safeStorage.decryptString(data);
      } else {
        return data.toString('utf8');
      }
    } catch (e) {
      console.error('Failed to get token:', e);
      return null;
    }
  }

  static clear(): void {
    try {
      if (fs.existsSync(TOKEN_PATH)) {
        fs.unlinkSync(TOKEN_PATH);
      }
    } catch (e) {
      console.error('Failed to clear token:', e);
    }
  }
}
