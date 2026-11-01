// Shared test setup: every test fails on an uncaught page error.
import { expect, test as base } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await use(page);
    expect(errors, 'uncaught page errors').toEqual([]);
  },
});

export { expect };
