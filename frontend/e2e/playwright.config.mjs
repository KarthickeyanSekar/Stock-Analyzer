// Browser end-to-end tests. Run with `make e2e`: a throwaway stack (db + seeded api + web) in Docker.
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: '*.e2e.mjs',
  // The journal tests share one database, so they run in order.
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 30_000,
  outputDir: process.env.E2E_OUTPUT_DIR ?? 'results',
  reporter: [['list']],
  // Baselines are rendered in the Playwright Linux image (make e2e), so they match on every OS.
  snapshotPathTemplate: `${process.env.E2E_SNAPSHOT_DIR ?? 'snapshots'}/{arg}{ext}`,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    reducedMotion: 'reduce',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
