import { BrowserWindow, screen } from 'electron';
import Store from 'electron-store';

interface WindowState {
  width: number;
  height: number;
  x?: number;
  y?: number;
  isMaximized: boolean;
}

const DEFAULT_STATE: WindowState = {
  width: 1280,
  height: 800,
  isMaximized: false,
};

export class WindowStateManager {
  private store: Store<{ windowState: WindowState }>;
  private state: WindowState;
  private name: string;

  constructor(name: string) {
    this.name = name;
    this.store = new Store({ name: `window-state-${name}` });
    this.state = this.store.get('windowState', DEFAULT_STATE);
  }

  get x() { return this.state.x; }
  get y() { return this.state.y; }
  get width() { return this.state.width; }
  get height() { return this.state.height; }
  get isMaximized() { return this.state.isMaximized; }

  manage(window: BrowserWindow) {
    if (this.state.isMaximized) {
      window.maximize();
    }

    const updateState = () => {
      if (!window.isDestroyed()) {
        const isMaximized = window.isMaximized();
        if (!isMaximized) {
          const bounds = window.getBounds();
          this.state = {
            ...bounds,
            isMaximized,
          };
        } else {
          this.state.isMaximized = true;
        }
        this.saveState();
      }
    };

    window.on('resize', updateState);
    window.on('move', updateState);
    window.on('close', updateState);
  }

  private saveState() {
    this.store.set('windowState', this.state);
  }

  static getInitialBounds(name: string): Partial<WindowState> {
    const store = new Store<{ windowState: WindowState }>({ name: `window-state-${name}` });
    const state = store.get('windowState', DEFAULT_STATE) as WindowState;
    
    // Validate if the window is within any screen's bounds
    if (state.x !== undefined && state.y !== undefined) {
      const displays = screen.getAllDisplays();
      const isVisible = displays.some(display => {
        const { x, y, width, height } = display.bounds;
        return (
          state.x! >= x &&
          state.y! >= y &&
          state.x! + state.width <= x + width &&
          state.y! + state.height <= y + height
        );
      });

      if (!isVisible) {
        return { width: state.width, height: state.height };
      }
    }

    return state;
  }
}
