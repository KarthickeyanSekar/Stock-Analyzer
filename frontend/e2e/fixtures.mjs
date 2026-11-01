// Shared test setup: every test is signed in as the e2e admin (dev-only sign-in) and fails
// on an uncaught page error. Use `anonymousPage` for signed-out checks.
import { expect, test as base } from '@playwright/test';

export const ADMIN_EMAIL = 'admin@e2e.local';

async function signIn(request, email = ADMIN_EMAIL, inviteCode = null) {
  const response = await request.post('/api/auth/dev-login', {
    data: { email, invite_code: inviteCode },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
}

export const test = base.extend({
  page: async ({ page }, use) => {
    await signIn(page.request);
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await use(page);
    expect(errors, 'uncaught page errors').toEqual([]);
  },
  request: async ({ request }, use) => {
    await signIn(request);
    await use(request);
  },
  anonymousPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect, signIn };
