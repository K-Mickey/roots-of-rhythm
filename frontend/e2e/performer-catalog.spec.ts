import { expect, test } from '@playwright/test';

const CHARLIE_PARKER_ID = '01a01a72-1be4-763d-8892-9d922967d97d';
const COUNT_BASIE_ID = '01a01a72-1be5-7542-b935-47f2b3e1b5a3';
const BENNY_GOODMAN_ID = '01a01a72-1be5-7542-b935-47f33d83c2ab';
const LOUIS_ARMSTRONG_ID = '01a01a72-1be5-7542-b935-47f617f2cfd3';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

test('performer catalog lists seed performers and opens Charlie Parker', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto('/');
  await page.getByRole('link', { name: 'Исполнители' }).click();
  await expect(page).toHaveURL('/performers');
  await expect(
    page.getByRole('heading', { name: 'Исполнители' }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: /^Charlie Parker$/ }),
  ).toHaveAttribute('href', `/performers/${CHARLIE_PARKER_ID}`);
  await expect(
    page.getByRole('link', { name: /^Count Basie$/ }),
  ).toHaveAttribute('href', `/performers/${COUNT_BASIE_ID}`);
  await expect(
    page.getByRole('link', { name: /^Benny Goodman$/ }),
  ).toHaveAttribute('href', `/performers/${BENNY_GOODMAN_ID}`);
  await expect(
    page.getByRole('link', { name: /^Louis Armstrong$/ }),
  ).toHaveAttribute('href', `/performers/${LOUIS_ARMSTRONG_ID}`);

  await page.getByRole('link', { name: /^Charlie Parker$/ }).click();
  await expect(page).toHaveURL(`/performers/${CHARLIE_PARKER_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Charlie Parker' }),
  ).toBeVisible();
});
