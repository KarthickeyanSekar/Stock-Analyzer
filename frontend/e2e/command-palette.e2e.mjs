import { expect, test } from './fixtures.mjs';

test('Cmd/Ctrl+K finds a stock by name and opens it', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  await page.keyboard.press('ControlOrMeta+k');
  const palette = page.getByRole('dialog');
  await expect(palette).toBeVisible();

  await page.keyboard.type('infosys');
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/\/stocks\/INFY$/);
  await expect(page.getByRole('heading', { name: /INFY/ })).toBeVisible();
  await expect(palette).toBeHidden();
});

test('Cmd/Ctrl+K opens a page', async ({ page }) => {
  await page.goto('/stocks', { waitUntil: 'networkidle' });
  await page.keyboard.press('ControlOrMeta+k');
  await page.keyboard.type('journal');
  await page.keyboard.press('Enter');

  await expect(page).toHaveURL(/\/journal$/);
});

test('Escape closes the palette without navigating', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  await page.keyboard.press('ControlOrMeta+k');
  await expect(page.getByRole('dialog')).toBeVisible();

  await page.keyboard.press('Escape');

  await expect(page.getByRole('dialog')).toBeHidden();
  await expect(page).toHaveURL(/\/$/);
});
