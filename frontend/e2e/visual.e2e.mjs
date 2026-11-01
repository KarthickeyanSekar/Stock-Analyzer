// Visual regression: every screen in light and dark compared with the committed baselines
// in e2e/snapshots. After an intended UI change: `make e2e-update`, review the new PNGs, commit.
import { expect, test } from './fixtures.mjs';

const SCREENS = [
  ['home', '/'],
  ['stocks', '/stocks'],
  ['stock', '/stocks/RELIANCE'],
  ['journal', '/journal'],
  ['settings', '/settings'],
  ['providers', '/admin/providers'],
];
// After NSE close on the last synthetic trading day, so the market status never changes.
const FIXED_NOW = new Date('2026-10-30T16:00:00+05:30');

for (const colorScheme of ['light', 'dark']) {
  test.describe(`${colorScheme} theme`, () => {
    test.use({ colorScheme, viewport: { width: 1440, height: 900 } });

    for (const [name, path] of SCREENS) {
      test(`${name} matches the baseline`, async ({ page }) => {
        await page.clock.setFixedTime(FIXED_NOW);
        await page.goto(path, { waitUntil: 'networkidle' });
        await page.waitForTimeout(500);
        await expect(page).toHaveScreenshot(`${name}-${colorScheme}.png`, {
          fullPage: true,
          animations: 'disabled',
          // An absolute pixel budget: a ratio would let a changed number (a few hundred px) slip by.
          maxDiffPixels: 50,
        });
      });
    }
  });
}
