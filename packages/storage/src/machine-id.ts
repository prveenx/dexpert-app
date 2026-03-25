import { execSync } from 'child_process';
import { createHash } from 'crypto';
import * as os from 'os';
import * as fs from 'fs';

/**
 * Generates a robust, immutable hardware fingerprint.
 * Survives app uninstalls and standard OS resets.
 */
export function getMachineId(): string {
  let hardwareId = '';

  try {
    const osPlatform = os.platform();
    
    if (osPlatform === 'win32') {
      // Windows: Get Motherboard UUID
      try {
        hardwareId = execSync('powershell.exe -NoProfile -Command "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"', { encoding: 'utf8' });
      } catch (e) {
        hardwareId = execSync('wmic csproduct get uuid', { encoding: 'utf8' }).split('\n')[1];
      }
    } else if (osPlatform === 'darwin') {
      // macOS: Get IOPlatformUUID
      hardwareId = execSync('ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID', { encoding: 'utf8' });
      hardwareId = hardwareId.split('=')[1].replace(/"/g, '').trim();
    } else if (osPlatform === 'linux') {
      // Linux: Machine ID
      try {
        hardwareId = fs.readFileSync('/etc/machine-id', 'utf8');
      } catch (e) {
        try {
          hardwareId = fs.readFileSync('/var/lib/dbus/machine-id', 'utf8');
        } catch (e2) {
          hardwareId = execSync('hostname', { encoding: 'utf8' });
        }
      }
    }
  } catch (error) {
    console.error('[Storage] Failed to get hardware ID, falling back to OS basics', error);
    hardwareId = `${process.env.USERNAME || process.env.USER}-${os.hostname()}`;
  }

  // Hash the ID so we never send raw hardware data over the network (Privacy by Design)
  return createHash('sha256')
    .update(hardwareId.trim())
    .digest('hex');
}