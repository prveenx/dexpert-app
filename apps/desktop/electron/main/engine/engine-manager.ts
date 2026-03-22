// ── Engine Manager ─────────────────────────────────────
// Spawns and manages the Python engine subprocess.
// ───────────────────────────────────────────────────────

import { ChildProcess, spawn } from 'child_process';
import { join } from 'path';
import { existsSync } from 'fs';
import { EventEmitter } from 'events';
import { findFreePort } from './engine-port';

export class EngineManager extends EventEmitter {
  private process: ChildProcess | null = null;
  private port: number = 48765;
  private restartCount: number = 0;
  private maxRestarts: number = 5;
  private isShuttingDown: boolean = false;

  async start(): Promise<void> {
    this.port = await findFreePort(48765);
    const pythonPath = this.findPython();
    const engineDir = this.getEngineDir();
    const mainPy = join(engineDir, 'main.py');

    if (!existsSync(mainPy)) {
      console.warn('[EngineManager] Engine main.py not found at:', mainPy);
      this.emit('stopped', 'not_found');
      return;
    }

    console.log(`[EngineManager] Starting engine on port ${this.port}...`);

    this.process = spawn(pythonPath, [mainPy], {
      cwd: engineDir,
      env: {
        ...process.env,
        ENGINE_PORT: String(this.port),
        ENGINE_HOST: '127.0.0.1',
        PYTHONUNBUFFERED: '1',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    this.process.stdout?.on('data', (data: Buffer) => {
      const text = data.toString();
      console.log('[Engine]', text.trim());
      if (text.includes('Application startup complete')) {
        this.restartCount = 0;
        this.emit('ready', this.port);
      }
    });

    this.process.stderr?.on('data', (data: Buffer) => {
      console.error('[Engine:err]', data.toString().trim());
    });

    this.process.on('exit', (code) => {
      console.log(`[EngineManager] Engine exited with code ${code}`);
      if (!this.isShuttingDown && this.restartCount < this.maxRestarts) {
        const delay = Math.min(1000 * Math.pow(2, this.restartCount), 16000);
        this.restartCount++;
        console.log(`[EngineManager] Restarting in ${delay}ms (attempt ${this.restartCount})...`);
        setTimeout(() => this.start(), delay);
        this.emit('crash', code);
      } else if (!this.isShuttingDown) {
        this.emit('stopped', 'max_restarts');
      }
    });
  }

  async stop(): Promise<void> {
    this.isShuttingDown = true;
    if (this.process && !this.process.killed) {
      this.process.kill('SIGTERM');
      // Wait up to 5 seconds for graceful shutdown
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          if (this.process && !this.process.killed) {
            this.process.kill('SIGKILL');
          }
          resolve();
        }, 5000);
        this.process?.on('exit', () => {
          clearTimeout(timeout);
          resolve();
        });
      });
    }
    this.process = null;
    this.emit('stopped', 'shutdown');
  }

  getPort(): number {
    return this.port;
  }

  private findPython(): string {
    const engineDir = this.getEngineDir();

    // Check for .venv first
    const venvPython = process.platform === 'win32'
      ? join(engineDir, '.venv', 'Scripts', 'python.exe')
      : join(engineDir, '.venv', 'bin', 'python');

    if (existsSync(venvPython)) {
      return venvPython;
    }

    // Fall back to system Python
    return process.platform === 'win32' ? 'python' : 'python3';
  }

  private getEngineDir(): string {
    // In development, engine is at the monorepo root
    // In production, it's bundled alongside the app
    const devPath = join(__dirname, '..', '..', '..', '..', 'engine');
    if (existsSync(devPath)) {
      return devPath;
    }
    return join(process.resourcesPath, 'engine');
  }
}
