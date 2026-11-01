import { expect, test } from './fixtures.mjs';

test('stock page: short-term tab, setup label and outlook card', async ({ page }) => {
  await page.goto('/stocks/INFY', { waitUntil: 'networkidle' });
  const outlook = page.locator('[data-slot="card"]').filter({ hasText: 'Outlook' });
  await expect(outlook.getByText('Next 5 days')).toBeVisible();
  await expect(outlook.getByText('1 year')).toBeVisible();
  await expect(outlook.getByText(/Favourable|Neutral|Unfavourable/)).toBeVisible();

  await page.getByRole('group', { name: 'Horizon' }).getByText('Short-term (1–10 days)').click();
  const periods = page.getByRole('listbox', { name: 'Holding periods' }).getByRole('option');
  await expect(periods).toHaveCount(4);
  await expect(periods.first()).toContainText('1D');
  await expect(page.getByRole('group', { name: 'Target' }).getByText('+2%')).toBeVisible();
  await expect(page.getByText('before a −3% stop')).toBeVisible();
});

test('a short plan defaults to the −3% stop and ends in sessions', async ({ page, request }) => {
  await page.goto('/stocks/HCLTECH', { waitUntil: 'networkidle' });
  await page.getByRole('group', { name: 'Horizon' }).getByText('Short-term (1–10 days)').click();
  await page
    .getByRole('button', { name: /^Start plan$/ })
    .first()
    .click();
  const sheet = page.getByRole('dialog');
  await expect(sheet.getByLabel('Stop-loss %')).toHaveValue('-3');
  await sheet.getByRole('button', { name: /^Start 5D plan$/ }).click();
  await expect(page.getByText(/Plan #\d+ started for HCLTECH/)).toBeVisible();

  const plans = await (await request.get('/api/trade-plans')).json();
  const plan = plans.find((p) => p.symbol === 'HCLTECH');
  expect(plan.category).toBe('5D');
  expect(plan.stop_pct).toBe(-3);
});

test('screener works for short holds', async ({ page }) => {
  await page.goto('/screener', { waitUntil: 'networkidle' });
  await page
    .getByRole('group', { name: 'Holding period' })
    .getByText('5D', { exact: true })
    .click();
  await expect(
    page.getByText(/\d+ stocks · hold 5D · chance of \+2% before a −3% stop/),
  ).toBeVisible();
  await expect(page.getByRole('group', { name: 'Target return' }).getByText('+1%')).toBeVisible();
  expect(await page.locator('table tbody tr').count()).toBeGreaterThan(0);
});
