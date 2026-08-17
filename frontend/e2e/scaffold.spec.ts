import { expect, test } from '@playwright/test';

test('serves frontend and backend health', async ({ page, request }) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Roots of Rhythm' }),
  ).toBeVisible();

  const backendUrl = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';
  const response = await request.get(`${backendUrl}/health/ready`);

  expect(response.ok()).toBe(true);
  await expect(response.json()).resolves.toEqual({ status: 'ok' });
});
