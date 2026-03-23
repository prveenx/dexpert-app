// electron.vite.config.ts
import { resolve } from "path";
import { defineConfig, externalizeDepsPlugin } from "electron-vite";
import react from "@vitejs/plugin-react";
var __electron_vite_injected_dirname = "C:\\Users\\user\\Desktop\\dexpert_desktop\\apps\\desktop";
var electron_vite_config_default = defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: "out/main",
      lib: {
        entry: resolve(__electron_vite_injected_dirname, "electron/main/index.ts")
      }
    },
    resolve: {
      alias: {
        "@dexpert/types": resolve(__electron_vite_injected_dirname, "../../packages/types/src")
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      outDir: "out/preload",
      lib: {
        entry: resolve(__electron_vite_injected_dirname, "electron/preload/index.ts")
      }
    }
  },
  renderer: {
    root: resolve(__electron_vite_injected_dirname, "src"),
    build: {
      outDir: resolve(__electron_vite_injected_dirname, "out/renderer"),
      rollupOptions: {
        input: resolve(__electron_vite_injected_dirname, "src/index.html")
      }
    },
    plugins: [react()],
    resolve: {
      alias: {
        "@": resolve(__electron_vite_injected_dirname, "src"),
        "@dexpert/types": resolve(__electron_vite_injected_dirname, "../../packages/types/src"),
        "@dexpert/ui": resolve(__electron_vite_injected_dirname, "../../packages/ui/src")
      }
    }
  }
});
export {
  electron_vite_config_default as default
};
