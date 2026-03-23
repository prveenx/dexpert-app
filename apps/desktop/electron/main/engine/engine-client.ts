// ── Engine WebSocket Client ────────────────────────────
// Main process ↔ engine communication via WebSocket.
// ───────────────────────────────────────────────────────

import WebSocket from 'ws';
import { EventEmitter } from 'events';
import type { ClientMessage, EngineEvent } from '@dexpert/types';

export class EngineClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private messageQueue: ClientMessage[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay: number = 1000;
  private maxReconnectDelay: number = 16000;
  private token: string | null = null;
  private isConnecting: boolean = false;

  constructor(port: number, token?: string | null) {
    super();
    this.token = token || null;
    this.url = `ws://127.0.0.1:${port}/ws`;
    if (this.token) {
      this.url += `?token=${this.token}`;
    }
  }

  connect(): void {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.on('open', () => {
        this.isConnecting = false;
        this.reconnectDelay = 1000;
        console.log('[EngineClient] Connected');
        this.emit('connected');

        // Flush queued messages
        while (this.messageQueue.length > 0) {
          const msg = this.messageQueue.shift()!;
          this.ws!.send(JSON.stringify(msg));
        }
      });

      this.ws.on('message', (data: WebSocket.Data) => {
        try {
          const event: EngineEvent = JSON.parse(data.toString());
          this.emit('event', event);
        } catch (err) {
          console.error('[EngineClient] Failed to parse message:', err);
        }
      });

      this.ws.on('close', () => {
        this.isConnecting = false;
        console.log('[EngineClient] Disconnected');
        this.emit('disconnected');
        this.scheduleReconnect();
      });

      this.ws.on('error', (err) => {
        this.isConnecting = false;
        console.error('[EngineClient] Error:', err.message);
      });
    } catch {
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  send(msg: ClientMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      this.messageQueue.push(msg);
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  setToken(token: string): void {
    this.token = token;
    // Update URL
    const baseUrl = this.url.split('?')[0];
    this.url = `${baseUrl}?token=${token}`;
    
    // Reconnect if currently connected or connecting with old/no token
    if (this.ws) {
      console.log('[EngineClient] Token updated, reconnecting...');
      this.disconnect();
      this.connect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
      this.connect();
    }, this.reconnectDelay);
  }
}
