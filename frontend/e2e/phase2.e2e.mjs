import { expect, test } from './fixtures.mjs';

test.describe.configure({ mode: 'serial' });

const DEFAULTS = {
  paper_capital: 1000000,
  risk_pct: 1,
  success_tolerance_pp: 0.5,
  default_stop_pct: -7,
};

test.afterAll(async ({ request }) => {
  await request.put('/api/settings/journal', { data: DEFAULTS });
});

test('settings change the defaults and the suggested position of new plans', async ({ page }) => {
  await page.goto('/settings', { waitUntil: 'networkidle' });
  await page.getByLabel('Risk per plan %').fill('2');
  await page.getByLabel('Default stop-loss %').fill('-10');
  await page.getByRole('button', { name: 'Save settings' }).click();
  await expect(page.getByText('Settings saved')).toBeVisible();

  await page.goto('/stocks/TCS', { waitUntil: 'networkidle' });
  await page
    .getByRole('button', { name: /^Start plan$/ })
    .first()
    .click();
  const sheet = page.getByRole('dialog');
  await expect(sheet.getByLabel('Stop-loss %')).toHaveValue('-10');
  await expect(sheet.getByText(/at 2% risk/)).toBeVisible();
  // 2% of 10,00,000 at a 10% stop = 2,00,000 budget, sized server-side.
  await expect(sheet.getByText('Suggested position').locator('..')).toContainText('sh');
});

test('a typed entry price is stored as MANUAL next to the close (Q29)', async ({
  page,
  request,
}) => {
  await page.goto('/stocks/ITC', { waitUntil: 'networkidle' });
  await page
    .getByRole('button', { name: /^Start plan$/ })
    .first()
    .click();
  const sheet = page.getByRole('dialog');
  const close = Number(await sheet.getByLabel('Entry ₹').inputValue());
  await sheet.getByLabel('Entry ₹').fill((close + 1).toFixed(2));
  await sheet.getByRole('button', { name: /^Start .* plan$/ }).click();
  await expect(page.getByText(/Plan #\d+ started for ITC/)).toBeVisible();

  const plans = await (await request.get('/api/trade-plans')).json();
  const plan = plans.find((p) => p.symbol === 'ITC');
  expect(plan.entry_source).toBe('MANUAL');
  expect(plan.reference_close).toBe(close);
  expect(plan.entry_price).toBeCloseTo(close + 1, 2);
});

test('active plans show day N of M and labelled tracking flags', async ({ page, request }) => {
  // A 50D plan started in 2025 has run past its end date in the synthetic data.
  const response = await request.post('/api/trade-plans', {
    data: { symbol: 'HDFCBANK', category: '50D', start_date: '2025-01-06', target_pct: 1 },
  });
  expect(response.ok()).toBeTruthy();

  await page.goto('/journal', { waitUntil: 'networkidle' });
  const card = page.getByRole('listitem').filter({ hasText: 'HDFCBANK' });
  await expect(card.getByText(/day \d+ of \d+/)).toBeVisible();
  await expect(card.getByText('End date reached')).toBeVisible();
  await expect(card.getByText(/Target reached|Stop-loss crossed/).first()).toBeVisible();
  await expect(card.getByRole('progressbar')).toBeVisible();
});

test('track record shows rates and actual vs predicted', async ({ page }) => {
  await page.goto('/journal', { waitUntil: 'networkidle' });
  await page.getByRole('tab', { name: 'Track record' }).click();

  await expect(page.getByText('Model success rate')).toBeVisible();
  await expect(page.getByText('Your targets reached')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Actual vs predicted' })).toBeVisible();
  await expect(page.getByRole('table')).toContainText('RELIANCE');
});
