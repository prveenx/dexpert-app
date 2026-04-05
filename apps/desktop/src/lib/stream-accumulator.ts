// ── Stream Accumulator ─────────────────────────────────
// Batches streaming tokens using requestAnimationFrame to
// prevent excessive React re-renders during token-level streaming.
//
// Instead of updating state per-token (50-100 re-renders/sec),
// this accumulates chunks and flushes once per animation frame (~60fps).
// ───────────────────────────────────────────────────────

export type FlushCallback = (accumulated: string) => void;

export class StreamAccumulator {
  private buffer: string[] = [];
  private rafId: number | null = null;
  private onFlush: FlushCallback;
  private isActive = false;

  constructor(onFlush: FlushCallback) {
    this.onFlush = onFlush;
  }

  /**
   * Push a token chunk into the buffer.
   * Schedules a flush on the next animation frame if not already scheduled.
   */
  push(chunk: string): void {
    this.buffer.push(chunk);
    this.isActive = true;

    if (this.rafId === null) {
      this.rafId = requestAnimationFrame(() => this.flush());
    }
  }

  /**
   * Flush all buffered chunks as a single merged string.
   */
  private flush(): void {
    if (this.buffer.length === 0) {
      this.rafId = null;
      return;
    }

    const merged = this.buffer.join('');
    this.buffer = [];
    this.rafId = null;
    this.onFlush(merged);
  }

  /**
   * Force an immediate flush of any pending chunks.
   */
  forceFlush(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.flush();
  }

  /**
   * Reset the accumulator. Cancels any pending flush.
   */
  reset(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.buffer = [];
    this.isActive = false;
  }

  /**
   * Whether this accumulator is currently receiving tokens.
   */
  get active(): boolean {
    return this.isActive;
  }
}

/**
 * Manages multiple stream accumulators keyed by session ID.
 * Each session gets its own independent accumulator.
 */
export class StreamManager {
  private accumulators: Map<string, StreamAccumulator> = new Map();
  private flushHandler: (sessionId: string, content: string) => void;

  constructor(onFlush: (sessionId: string, content: string) => void) {
    this.flushHandler = onFlush;
  }

  /**
   * Push a token chunk for a specific session.
   */
  push(sessionId: string, chunk: string): void {
    let acc = this.accumulators.get(sessionId);
    if (!acc) {
      acc = new StreamAccumulator((content) => {
        this.flushHandler(sessionId, content);
      });
      this.accumulators.set(sessionId, acc);
    }
    acc.push(chunk);
  }

  /**
   * Finalize a session's stream, flushing remaining chunks.
   */
  finalize(sessionId: string): void {
    const acc = this.accumulators.get(sessionId);
    if (acc) {
      acc.forceFlush();
      acc.reset();
      this.accumulators.delete(sessionId);
    }
  }

  /**
   * Reset all accumulators.
   */
  resetAll(): void {
    this.accumulators.forEach(acc => acc.reset());
    this.accumulators.clear();
  }
}
