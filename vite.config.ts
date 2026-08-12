import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    preserveSymlinks: true,
  },
  optimizeDeps: {
    esbuildOptions: {
      preserveSymlinks: true,
    },
  },
  server: {
    port: 5173,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./frontend/src/test-setup.ts"],
    include: ["frontend/src/**/*.test.{ts,tsx}"],
    pool: "threads",
    maxWorkers: 1,
    minWorkers: 1,
    fileParallelism: false,
    isolate: false,
  },
});
