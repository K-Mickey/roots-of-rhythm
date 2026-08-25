import { expect, test } from '@playwright/test';

const BENNY_GOODMAN_ORCHESTRA_ID = '01a01a72-2c01-7000-8000-000000000001';
const CHARLIE_PARKER_QUINTET_ID = '01a01a72-2c01-7000-8000-000000000002';
const COUNT_BASIE_ORCHESTRA_ID = '01a01a72-2c01-7000-8000-000000000003';
const TYMPANY_FIVE_ID = '01a01a72-2c01-7000-8000-000000000004';
const COUNT_BASIE_ID = '01a01a72-1be5-7542-b935-47f2b3e1b5a3';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

test('group catalog lists seed groups and opens Count Basie Orchestra', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto('/');
  await page.getByRole('link', { name: 'Группы' }).click();
  await expect(page).toHaveURL('/groups');
  await expect(page.getByRole('heading', { name: 'Группы' })).toBeVisible();
  await expect(
    page.getByRole('link', { name: /^Benny Goodman Orchestra$/ }),
  ).toHaveAttribute('href', `/groups/${BENNY_GOODMAN_ORCHESTRA_ID}`);
  await expect(
    page.getByRole('link', { name: /^Charlie Parker Quintet$/ }),
  ).toHaveAttribute('href', `/groups/${CHARLIE_PARKER_QUINTET_ID}`);
  await expect(
    page.getByRole('link', { name: /^Count Basie Orchestra$/ }),
  ).toHaveAttribute('href', `/groups/${COUNT_BASIE_ORCHESTRA_ID}`);
  await expect(
    page.getByRole('link', { name: /^Tympany Five$/ }),
  ).toHaveAttribute('href', `/groups/${TYMPANY_FIVE_ID}`);

  await page.getByRole('link', { name: /^Count Basie Orchestra$/ }).click();
  await expect(page).toHaveURL(`/groups/${COUNT_BASIE_ORCHESTRA_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Count Basie Orchestra' }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Swing' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Count Basie' })).toHaveAttribute(
    'href',
    `/performers/${COUNT_BASIE_ID}`,
  );
  await expect(page.getByText('piano, bandleader')).toBeVisible();
});
