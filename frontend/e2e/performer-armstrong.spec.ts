import { expect, test } from '@playwright/test';

const LOUIS_ARMSTRONG_ID = '01a01a72-1be5-7542-b935-47f617f2cfd3';
const JAZZ_ID = '01a0147a-8508-74b7-9689-e7c079b95327';
const SWING_ID = '01a0147a-8508-74b7-9689-e7c133e4e7a5';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

test('seed Louis Armstrong page shows published genre links', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto(`/performers/${LOUIS_ARMSTRONG_ID}`);

  await expect(
    page.getByRole('heading', { level: 1, name: 'Louis Armstrong' }),
  ).toBeVisible();
  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByRole('contentinfo')).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Jazz', exact: true }),
  ).toHaveAttribute('href', `/genres/${JAZZ_ID}`);
  await expect(
    page.getByRole('link', { name: 'Swing', exact: true }),
  ).toHaveAttribute('href', `/genres/${SWING_ID}`);
});

test('Armstrong genre names open Jazz and Swing pages', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto(`/performers/${LOUIS_ARMSTRONG_ID}`);
  await page.getByRole('link', { name: 'Jazz', exact: true }).click();
  await expect(page).toHaveURL(`/genres/${JAZZ_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Jazz' }),
  ).toBeVisible();

  await page.goto(`/performers/${LOUIS_ARMSTRONG_ID}`);
  await page.getByRole('link', { name: 'Swing', exact: true }).click();
  await expect(page).toHaveURL(`/genres/${SWING_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Swing' }),
  ).toBeVisible();
});
