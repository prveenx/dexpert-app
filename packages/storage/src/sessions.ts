import { SecureVault } from './vault';
import type { Session, ConversationTurn } from '@dexpert/types';

export interface SessionData {
  sessions: Session[];
  currentSessionId: string | null;
  messages: ConversationTurn[];
}

export class SessionPersistence {
  private vault: SecureVault;

  constructor() {
    this.vault = new SecureVault('sessions.enc');
  }

  /**
   * Loads all session data from the resilient vault.
   */
  public async load(): Promise<SessionData> {
    const data = this.vault.get();
    if (!data) {
      return {
        sessions: [],
        currentSessionId: null,
        messages: [],
      };
    }
    return data as SessionData;
  }

  /**
   * Persists the entire session state to the resilient vault.
   * Survives app uninstalls and data purges via home directory backup.
   */
  public async save(data: SessionData): Promise<void> {
    this.vault.set(data);
  }

  /**
   * Partial updates for efficiency if needed.
   */
  public async patch(patch: Partial<SessionData>): Promise<void> {
    const current = await this.load();
    const updated = { ...current, ...patch };
    await this.save(updated);
  }

  public async clear(): Promise<void> {
    this.vault.clear();
  }
}
