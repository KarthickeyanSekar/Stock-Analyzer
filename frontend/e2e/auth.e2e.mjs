import { expect, signIn, test } from './fixtures.mjs';

test('signed-out visitors are sent to the sign-in page', async ({ anonymousPage }) => {
  await anonymousPage.goto('/journal');
  await expect(anonymousPage).toHaveURL(/\/sign-in$/);
  await expect(anonymousPage.getByText('Sign in to Stock Analyzer')).toBeVisible();
  await expect(anonymousPage.getByText('Developer sign-in (local only)')).toBeVisible();
});

test('an invite lets a new user in, without admin pages', async ({ page, anonymousPage }) => {
  await page.goto('/admin/users', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'New code' }).click();
  const code = (await page.locator('li .font-mono').first().textContent()).trim();
  expect(code).toMatch(/^SA-[A-Z2-9]{4}-[A-Z2-9]{4}$/);

  await anonymousPage.goto(`/sign-in?code=${code}`);
  await expect(anonymousPage.getByLabel('Invite code (new accounts only)')).toHaveValue(code);
  await anonymousPage.getByLabel('Developer sign-in (local only)').fill('friend@e2e.local');
  await anonymousPage.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(anonymousPage).toHaveURL(/\/$/);
  await expect(anonymousPage.getByRole('link', { name: 'Journal' }).first()).toBeVisible();
  await expect(anonymousPage.getByRole('link', { name: 'Users' })).toHaveCount(0);

  await anonymousPage.goto('/admin/users');
  await expect(anonymousPage).toHaveURL(/\/$/); // not for users

  // The code is used up now.
  await page.reload({ waitUntil: 'networkidle' });
  await expect(page.locator('li').filter({ hasText: code }).getByText('Used')).toBeVisible();
});

test('a user can read the privacy notice and delete their account', async ({
  page,
  anonymousPage,
}) => {
  const response = await page.request.post('/api/admin/invites', {
    data: { max_uses: 1, valid_days: 7, role: 'user' },
  });
  const { code } = await response.json();
  await signIn(anonymousPage.request, 'leaving@e2e.local', code);

  await anonymousPage.goto('/', { waitUntil: 'networkidle' });
  await anonymousPage.getByRole('button', { name: 'Account' }).click();
  await anonymousPage.getByRole('menuitem', { name: 'Privacy notice' }).click();
  await expect(anonymousPage.getByRole('heading', { name: 'Privacy notice' })).toBeVisible();

  await anonymousPage.goto('/', { waitUntil: 'networkidle' });
  await anonymousPage.getByRole('button', { name: 'Account' }).click();
  await anonymousPage.getByRole('menuitem', { name: 'Delete my account' }).click();
  await anonymousPage.getByRole('button', { name: 'Delete everything' }).click();
  await expect(anonymousPage).toHaveURL(/\/sign-in$/);

  const me = await anonymousPage.request.get('/api/auth/me');
  expect(me.status()).toBe(401);
});

test('the star adds a stock to the watchlist', async ({ page, request }) => {
  await page.goto('/stocks/WIPRO', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Add WIPRO to watchlist' }).click();
  await expect(page.getByRole('button', { name: 'Remove WIPRO from watchlist' })).toBeVisible();

  const symbols = (await (await request.get('/api/watchlist')).json()).map((s) => s.symbol);
  expect(symbols).toContain('WIPRO');
  await page.getByRole('button', { name: 'Remove WIPRO from watchlist' }).click();
  await expect(page.getByRole('button', { name: 'Add WIPRO to watchlist' })).toBeVisible();
});
