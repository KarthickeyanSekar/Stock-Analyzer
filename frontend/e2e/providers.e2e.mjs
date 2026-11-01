import { expect, test } from './fixtures.mjs';

// A fake key: the e2e stack has no real EODHD account, so the test only proves the key is
// stored write-only and that the connection test reports a readable result.
const FAKE_KEY = 'e2e-fake-key-7q7q';

test.afterAll(async ({ request }) => {
  await request.put('/api/admin/providers/mock/primary');
  await request.delete('/api/admin/providers/eodhd/credentials');
});

test('the EODHD key is write-only and the test reports a result', async ({ page }) => {
  await page.goto('/admin/providers', { waitUntil: 'networkidle' });
  const card = page.locator('[data-slot="card"]').filter({ hasText: 'EODHD' });
  await expect(card.getByText('Standby')).toBeVisible();
  await expect(card.getByRole('button', { name: 'Use as primary' })).toBeDisabled();

  await card.getByLabel('API key', { exact: true }).fill(FAKE_KEY);
  await card.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByText('API key saved (encrypted)')).toBeVisible();

  const field = card.getByLabel('API key', { exact: true });
  await expect(field).toHaveValue('');
  await expect(field).toHaveAttribute('placeholder', '•••• 7q7q (saved)');
  expect(await page.content()).not.toContain(FAKE_KEY);

  await card.getByRole('button', { name: 'Test connection' }).click();
  await expect(card.getByRole('status')).toContainText(/OK|Failed/);
  expect(await page.content()).not.toContain(FAKE_KEY);

  await expect(card.getByRole('button', { name: 'Use as primary' })).toBeEnabled();
  await card.getByRole('button', { name: 'Remove API key' }).click();
  await expect(page.getByText('API key removed')).toBeVisible();
  await expect(card.getByLabel('API key', { exact: true })).toHaveAttribute(
    'placeholder',
    'Paste the key',
  );
});
