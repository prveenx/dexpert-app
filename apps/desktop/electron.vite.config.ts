import { resolve } from 'path';
import { defineConfig, externalizeDepsPlugin } from 'electron-vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin({
      exclude: ['@dexpert/storage', '@dexpert/types']
    })],
    build: {
      outDir: 'out/main',
      lib: {
        entry: resolve(__dirname, 'electron/main/index.ts'),
      },
    },
    resolve: {
      alias: {
        '@dexpert/types': resolve(__dirname, '../../packages/types/src'),
        '@dexpert/storage': resolve(__dirname, '../../packages/storage/src'),
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: 'out/preload',
      lib: {
        entry: resolve(__dirname, 'electron/preload/index.ts'),
      },
    },
  },
  renderer: {
    root: resolve(__dirname, 'src'),
    build: {
      outDir: resolve(__dirname, 'out/renderer'),
      rollupOptions: {
        input: resolve(__dirname, 'src/index.html'),
      },
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@dexpert/types': resolve(__dirname, '../../packages/types/src'),
        '@dexpert/ui': resolve(__dirname, '../../packages/ui/src'),
        '@dexpert/storage': resolve(__dirname, '../../packages/storage/src'),
      },
    },
  },
});
