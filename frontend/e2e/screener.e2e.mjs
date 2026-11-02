import { expect, test } from './fixtures.mjs';

test('screener ranks stocks and explains an empty result', async ({ page }) => {
  await page.goto('/screener', { waitUntil: 'networkidle' });
  const summary = page.getByText(/\d+ stocks · hold 1Y/);
  await expect(summary).toBeVisible();
  const rows = page.locator('table tbody tr');
  expect(await rows.count()).toBeGreaterThan(0);

  // An impossible wish → empty state with a way back.
  await page.getByRole('group', { name: 'Target return' }).getByText('+50%').click();
  await page.getByLabel('Chance at least').click();
  await page.getByRole('option', { name: '60%' }).click();
  await expect(page.getByText('No stocks match')).toBeVisible();
  await page.getByRole('button', { name: 'Clear filters' }).click();
  await expect(page.getByText('No stocks match')).toBeHidden();

  await page.getByRole('group', { name: 'Target return' }).getByText('+10%').click();
  const first = rows.first().getByRole('link');
  const symbol = await first.textContent();
  await first.click();
  await expect(page).toHaveURL(new RegExp(`/stocks/${symbol}$`));
});

test('stock page shows similar past setups', async ({ page }) => {
  await page.goto('/stocks/INFY', { waitUntil: 'networkidle' });
  const card = page.locator('[data-slot="card"]').filter({ hasText: 'Similar past setups' });

  await expect(card.getByText('Median')).toBeVisible();
  await expect(card.getByRole('listitem').first()).toBeVisible();
});

test('screener table sorts, searches and pages', async ({ page }) => {
  await page.goto('/screener', { waitUntil: 'networkidle' });
  const table = page.getByRole('table', { name: 'Screener results' });
  await expect(page.getByText('1–25 of 50')).toBeVisible();
  await expect(table.locator('tbody tr')).toHaveCount(25);

  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByText('26–50 of 50')).toBeVisible();
  await expect(page.getByText('Page 2 of 2')).toBeVisible();

  // Paging leaves the window scrolled down, where the sticky app header covers the table header.
  await page.evaluate(() => {
    window.scrollTo(0, 0);
  });
  const sortMedian = table.getByRole('button', { name: 'Median', exact: true });
  const median = table.locator('th').filter({ hasText: /^Median$/ });
  await sortMedian.click();
  await expect(median).toHaveAttribute('aria-sort', 'descending');
  await expect(page.getByText('Page 1 of 2')).toBeVisible(); // sorting returns to page 1

  await page.getByLabel('Search results').fill('infy');
  await expect(table.locator('tbody tr')).toHaveCount(1);
  await expect(table.locator('tbody tr').first()).toContainText('INFY');
  await expect(page.getByText('1–1 of 1')).toBeVisible();
});
