import { expect, test } from '@playwright/test';

test('home shows product identity and not-found returns to it', async ({
  page,
}) => {
  await page.goto('/');

  await expect(
    page.getByRole('heading', { name: 'Roots of Rhythm' }),
  ).toBeVisible();
  await expect(
    page.getByText('История музыки для тех кто танцует и слушает'),
  ).toBeVisible();
  await expect(page.locator('a[href*="/genres/"]')).toHaveCount(0);
  await expect(page.locator('a[href*="/performers/"]')).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Жанры' })).toHaveAttribute(
    'href',
    '/genres',
  );
  await expect(page.getByRole('link', { name: 'Исполнители' })).toHaveAttribute(
    'href',
    '/performers',
  );

  await expect(
    page.getByRole('link', { name: 'Roots of Rhythm' }),
  ).toHaveAttribute('href', '/');

  await page.goto('/genres/00000000-0000-0000-0000-000000000000');
  await page.getByRole('link', { name: 'На главную' }).click();
  await expect(page).toHaveURL('/');
  await expect(
    page.getByRole('heading', { name: 'Roots of Rhythm' }),
  ).toBeVisible();
});
