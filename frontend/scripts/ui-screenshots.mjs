// Visual review: render every screen in a real browser (light, dark, phone) into ./screenshots.
// Run with `make ui-shots` (uses the Playwright Docker image; the app must be running: make dev).
import { mkdirSync } from 'node:fs';

import { chromium } from 'playwright';

const BASE = process.env.UI_BASE_URL ?? 'http://localhost:5173';
const OUT = process.env.UI_SHOTS_DIR ?? 'screenshots';
const SCREENS = [
  ['home', '/'],
  ['stocks', '/stocks'],
  ['stock', '/stocks/RELIANCE'],
  ['journal', '/journal'],
  ['providers', '/admin/providers'],
];
const VARIANTS = [
  { name: 'desktop-light', viewport: { width: 1440, height: 900 }, colorScheme: 'light' },
  { name: 'desktop-dark', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' },
  { name: 'phone-light', viewport: { width: 390, height: 844 }, colorScheme: 'light' },
];

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
const errors = [];
for (const variant of VARIANTS) {
  const context = await browser.newContext({ ...variant, reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.on('pageerror', (error) => errors.push(`${variant.name}: ${error.message}`));
  for (const [name, path] of SCREENS) {
    await page.goto(BASE + path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${OUT}/${name}-${variant.name}.png`, fullPage: true });
  }
  if (variant.name === 'desktop-light') {
    await page.goto(`${BASE}/stocks/RELIANCE`, { waitUntil: 'networkidle' });
    await page
      .getByRole('button', { name: /^Start plan$/ })
      .first()
      .click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${OUT}/start-plan-sheet-${variant.name}.png` });
  }
  await context.close();
}
await browser.close();
console.log(`Saved screenshots to ${OUT}/`);
if (errors.length > 0) {
  console.error(`Page errors:\n${errors.join('\n')}`);
  process.exit(1);
}
