import { expect, test } from '@playwright/test';

const SWING_ID = '01a0147a-8508-74b7-9689-e7c133e4e7a5';
const JAZZ_ID = '01a0147a-8508-74b7-9689-e7c079b95327';
const JUMP_BLUES_ID = '01a0147a-8508-74b7-9689-e7c272039bac';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

test('seed Swing genre page shows overview, relations, and sources', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto(`/genres/${SWING_ID}`);

  await expect(
    page.getByRole('heading', { level: 1, name: 'Swing' }),
  ).toBeVisible();
  await expect(page.getByRole('banner')).toBeVisible();
  await expect(page.getByRole('contentinfo')).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Jazz', exact: true }),
  ).toHaveAttribute('href', `/genres/${JAZZ_ID}`);
  await expect(
    page.getByRole('link', { name: 'Jump Blues', exact: true }),
  ).toHaveAttribute('href', `/genres/${JUMP_BLUES_ID}`);
  await expect(page.getByRole('heading', { name: 'Источники' })).toBeVisible();
});

test('Swing relation names open Jazz and Jump Blues pages', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto(`/genres/${SWING_ID}`);
  await page.getByRole('link', { name: 'Jazz', exact: true }).click();
  await expect(page).toHaveURL(`/genres/${JAZZ_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Jazz' }),
  ).toBeVisible();

  await page.goto(`/genres/${SWING_ID}`);
  await page.getByRole('link', { name: 'Jump Blues', exact: true }).click();
  await expect(page).toHaveURL(`/genres/${JUMP_BLUES_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Jump Blues' }),
  ).toBeVisible();
});
