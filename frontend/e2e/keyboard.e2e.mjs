import { expect, test } from './fixtures.mjs';

const PAGES = ['/', '/stocks', '/stocks/RELIANCE', '/journal', '/settings', '/admin/providers'];
const TAB_STOPS = 12;

for (const path of PAGES) {
  test(`every Tab stop on ${path} shows a visible focus indicator`, async ({ page }) => {
    await page.goto(path, { waitUntil: 'networkidle' });
    const missing = [];
    for (let i = 0; i < TAB_STOPS; i += 1) {
      await page.keyboard.press('Tab');
      const focus = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return null;
        const style = getComputedStyle(el);
        const hasOutline = style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0;
        const hasRing = style.boxShadow !== 'none';
        const label = el.getAttribute('aria-label') ?? el.textContent?.trim().slice(0, 40) ?? '';
        return { label: `${el.tagName.toLowerCase()} "${label}"`, visible: hasOutline || hasRing };
      });
      if (focus && !focus.visible) missing.push(focus.label);
    }
    expect(missing, 'focused elements without a visible indicator').toEqual([]);
  });
}

test('the start-plan sheet opens with Enter, takes focus and closes with Escape', async ({
  page,
}) => {
  await page.goto('/stocks/INFY', { waitUntil: 'networkidle' });
  const start = page.getByRole('button', { name: /^Start plan$/ }).first();
  await expect(start).toBeEnabled();
  await start.focus();
  await page.keyboard.press('Enter');

  const sheet = page.getByRole('dialog');
  await expect(sheet).toBeVisible();
  // Focus moves into the sheet and Escape closes it again.
  await expect(sheet.locator(':focus')).toHaveCount(1);
  await page.keyboard.press('Escape');
  await expect(sheet).toBeHidden();
});
