import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// In Docker the API is reachable as "api"; from VS Code on the host it is localhost.
const apiTarget = process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: { '/api': { target: apiTarget, changeOrigin: true } },
    // Test output is written into the mounted source; watching it reloads every open page.
    watch: { ignored: ['**/e2e-results/**', '**/screenshots/**', '**/e2e/snapshots/**'] },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
