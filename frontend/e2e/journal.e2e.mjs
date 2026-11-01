import { expect, test } from './fixtures.mjs';

const SYMBOL = 'RELIANCE';

async function activePlan(request) {
  const plans = await (await request.get('/api/trade-plans')).json();
  return plans.find((plan) => plan.symbol === SYMBOL && plan.status === 'ACTIVE');
}

test.describe.configure({ mode: 'serial' });

test('start a plan in the sheet: the prediction is locked', async ({ page, request }) => {
  await page.goto(`/stocks/${SYMBOL}`);
  await page
    .getByRole('button', { name: /^Start plan$/ })
    .first()
    .click();

  const sheet = page.getByRole('dialog');
  await expect(sheet.getByText(`Start a plan · ${SYMBOL}`)).toBeVisible();
  await sheet.getByRole('button', { name: /^1Y/ }).click();
  await expect(sheet.getByRole('button', { name: /^1Y/ })).toHaveAttribute('aria-pressed', 'true');
  await sheet.getByRole('button', { name: 'Start 1Y plan' }).click();

  await expect(page.getByText(new RegExp(`Plan #\\d+ started for ${SYMBOL}`))).toBeVisible();
  const plan = await activePlan(request);
  expect(plan).toMatchObject({ category: '1Y', status: 'ACTIVE' });
  expect(plan.prediction_id).not.toBeNull();
});

test('close dialog previews every outcome before confirming', async ({ page, request }) => {
  const plan = await activePlan(request);
  await page.goto('/journal');
  await page.getByRole('button', { name: 'Close plan' }).first().click();

  const dialog = page.getByRole('dialog');
  await expect(dialog.getByText(`Close plan #${plan.id} · ${SYMBOL}`)).toBeVisible();
  const exitPrice = dialog.getByLabel('Exit price (₹)');
  const preview = dialog.locator('[aria-live="polite"]');

  // Prefilled with the target price → within tolerance.
  await expect(preview).toContainText('Success');
  await exitPrice.fill((plan.target_price * 1.05).toFixed(2));
  await expect(preview).toContainText('Partial');
  await exitPrice.fill((plan.entry_price * 0.9).toFixed(2));
  await expect(preview).toContainText('Failure');

  await exitPrice.fill(plan.target_price.toFixed(2));
  await dialog.getByRole('button', { name: 'Close plan' }).click();

  await expect(page.getByText(`Plan #${plan.id} closed: SUCCESS`)).toBeVisible();
  const closed = await (await request.get(`/api/trade-plans/${plan.id}`)).json();
  expect(closed).toMatchObject({ status: 'CLOSED', outcome: 'SUCCESS' });
});

test('cancel leaves the plan open', async ({ page, request }) => {
  await page.goto(`/stocks/${SYMBOL}`);
  await page
    .getByRole('button', { name: /^Start plan$/ })
    .first()
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: /^Start .* plan$/ })
    .click();
  await expect(page.getByText(/Plan #\d+ started/)).toBeVisible();
  const plan = await activePlan(request);

  await page.goto('/journal');
  await page.getByRole('button', { name: 'Close plan' }).first().click();
  await page.getByRole('dialog').getByRole('button', { name: 'Cancel' }).click();

  await expect(page.getByRole('dialog')).toBeHidden();
  const still = await (await request.get(`/api/trade-plans/${plan.id}`)).json();
  expect(still.status).toBe('ACTIVE');
});
