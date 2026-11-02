import { expect, test } from './fixtures.mjs';

test('Ask AI menu opens without crashing the stock page', async ({ page }) => {
  await page.goto('/stocks/RELIANCE', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Ask AI' }).click();

  const menu = page.getByRole('menu');
  await expect(menu).toBeVisible();
  await expect(menu.getByText(/in a new tab/)).toBeVisible();
  expect(await menu.getByRole('menuitem').count()).toBeGreaterThan(0);
  await expect(page.getByText('Unexpected Application Error')).toHaveCount(0);
});
