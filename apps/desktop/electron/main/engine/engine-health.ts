import { BrowserWindow } from 'electron';
import { IPC } from '../ipc/channels';

export class EngineHealthMonitor {
  private port: number;
  private intervalId: NodeJS.Timeout | null = null;
  private status: 'healthy' | 'degraded' | 'offline' = 'offline';
  private windows: BrowserWindow[] = [];

  constructor(port: number) {
    this.port = port;
  }

  public registerWindow(window: BrowserWindow) {
    this.windows.push(window);
    // Remove window on close
    window.on('closed', () => {
      this.windows = this.windows.filter(w => w !== window);
    });
  }

  public start() {
    this.check();
    this.intervalId = setInterval(() => this.check(), 30000);
  }

  public stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private async check() {
    try {
      const response = await fetch(`http://127.0.0.1:${this.port}/api/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });

      if (response.ok) {
        this.updateStatus('healthy');
      } else {
        this.updateStatus('degraded');
      }
    } catch (err) {
      this.updateStatus('offline');
    }
  }

  private updateStatus(newStatus: 'healthy' | 'degraded' | 'offline') {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.broadcast();
    }
  }

  private broadcast() {
    this.windows.forEach(window => {
      if (!window.isDestroyed()) {
        window.webContents.send(IPC.ENGINE_EVENTS, {
          type: 'engine_health',
          status: this.status,
        });
      }
    });
  }

  public getStatus() {
    return this.status;
  }
}
