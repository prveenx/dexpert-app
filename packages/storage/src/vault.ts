import { safeStorage, app } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export class SecureVault {
  private primaryPath: string;
  private backupPath: string;

  constructor(filename: string = 'vault.enc', appName: string = 'dexpert') {
    // Primary: Standard AppData
    this.primaryPath = path.join(app.getPath('userData'), filename);
    // Resilient Backup: User Home Directory Dotfile (Survives standard uninstalls)
    this.backupPath = path.join(os.homedir(), `.${appName}-${filename}`);
  }

  /**
   * Encrypts and saves data resiliently.
   */
  public set(data: any): void {
    const jsonString = JSON.stringify(data);
    let bufferToWrite: Buffer;

    if (safeStorage.isEncryptionAvailable()) {
      bufferToWrite = safeStorage.encryptString(jsonString);
    } else {
      console.warn('[SecureVault] OS Encryption unavailable. Storing plaintext fallback.');
      bufferToWrite = Buffer.from(jsonString, 'utf-8');
    }

    // Write to both locations
    try {
      if (!fs.existsSync(path.dirname(this.primaryPath))) {
        fs.mkdirSync(path.dirname(this.primaryPath), { recursive: true });
      }
      fs.writeFileSync(this.primaryPath, bufferToWrite);
    } catch (e) {
      console.error('[SecureVault] Failed to write primary vault.', e);
    }

    try {
      fs.writeFileSync(this.backupPath, bufferToWrite);
    } catch (e) {
      console.warn('[SecureVault] Failed to write backup vault.', e);
    }
  }

  /**
   * Retrieves decrypted data.
   */
  public get(): any {
    let rawBuffer: Buffer | null = null;

    // Try primary first, then fallback to backup (if AppData was wiped)
    if (fs.existsSync(this.primaryPath)) {
      rawBuffer = fs.readFileSync(this.primaryPath);
    } else if (fs.existsSync(this.backupPath)) {
      rawBuffer = fs.readFileSync(this.backupPath);
      // Restore primary from backup
      try {
        if (!fs.existsSync(path.dirname(this.primaryPath))) {
          fs.mkdirSync(path.dirname(this.primaryPath), { recursive: true });
        }
        fs.writeFileSync(this.primaryPath, rawBuffer);
      } catch (e) {
        console.warn('[SecureVault] Failed to restore primary from backup.', e);
      }
    }

    if (!rawBuffer) return null;

    try {
      let jsonString: string;
      if (safeStorage.isEncryptionAvailable()) {
        jsonString = safeStorage.decryptString(rawBuffer);
      } else {
        jsonString = rawBuffer.toString('utf-8');
      }
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('[SecureVault] Failed to decrypt or parse vault data.', error);
      return null;
    }
  }

  /**
   * For legacy compatibility if needed, but 'get' and 'set' should be preferred for full state.
   */
  public getPartial(key: string): any {
    const data = this.get() || {};
    return data[key];
  }

  public setPartial(key: string, value: any): void {
    const data = this.get() || {};
    data[key] = value;
    this.set(data);
  }

  public clear(): void {
    if (fs.existsSync(this.primaryPath)) fs.unlinkSync(this.primaryPath);
    if (fs.existsSync(this.backupPath)) fs.unlinkSync(this.backupPath);
  }
}