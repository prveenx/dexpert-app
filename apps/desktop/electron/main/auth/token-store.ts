import { app } from 'electron';
import { SecureVault } from '@dexpert/storage';

const vault = new SecureVault('auth.enc');

export class TokenStore {
  static save(jwt: string): void {
    vault.set({ token: jwt });
  }

  static get(): string | null {
    const data = vault.get();
    return data?.token || null;
  }

  static clear(): void {
    vault.clear();
  }
}
