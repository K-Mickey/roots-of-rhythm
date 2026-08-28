import { expect, test } from '@playwright/test';

const SIXTEEN_TONS_ID = '01a01a72-3c01-7000-8000-000000000001';
const ONE_O_CLOCK_JUMP_ID = '01a01a72-3c01-7000-8000-000000000002';
const ORNITHOLOGY_ID = '01a01a72-3c01-7000-8000-000000000003';
const SING_SING_SING_ID = '01a01a72-3c01-7000-8000-000000000004';
const SHAKE_RATTLE_AND_ROLL_ID = '01a01a72-3c01-7000-8000-000000000005';
const WEST_END_BLUES_ID = '01a01a72-3c01-7000-8000-000000000006';
const MERLE_TRAVIS_ID = '01a01a72-3b01-7000-8000-000000000001';
const COUNT_BASIE_ID = '01a01a72-1be5-7542-b935-47f2b3e1b5a3';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://127.0.0.1:8000';

test('song catalog lists seed songs and opens Sixteen Tons with authors', async ({
  page,
  request,
}) => {
  const ready = await request.get(`${BACKEND_URL}/health/ready`);
  expect(ready.ok()).toBeTruthy();

  await page.goto('/');
  await page.getByRole('link', { name: 'Песни' }).click();
  await expect(page).toHaveURL('/songs');
  await expect(page.getByRole('heading', { name: 'Песни' })).toBeVisible();
  await expect(
    page.getByRole('link', { name: /^Sixteen Tons$/ }),
  ).toHaveAttribute('href', `/songs/${SIXTEEN_TONS_ID}`);
  await expect(
    page.getByRole('link', { name: /^One O'Clock Jump$/ }),
  ).toHaveAttribute('href', `/songs/${ONE_O_CLOCK_JUMP_ID}`);
  await expect(
    page.getByRole('link', { name: /^Ornithology$/ }),
  ).toHaveAttribute('href', `/songs/${ORNITHOLOGY_ID}`);
  await expect(
    page.getByRole('link', { name: /^Sing, Sing, Sing \(With a Swing\)$/ }),
  ).toHaveAttribute('href', `/songs/${SING_SING_SING_ID}`);
  await expect(
    page.getByRole('link', { name: /^Shake, Rattle and Roll$/ }),
  ).toHaveAttribute('href', `/songs/${SHAKE_RATTLE_AND_ROLL_ID}`);
  await expect(
    page.getByRole('link', { name: /^West End Blues$/ }),
  ).toHaveAttribute('href', `/songs/${WEST_END_BLUES_ID}`);

  await page.getByRole('link', { name: /^Sixteen Tons$/ }).click();
  await expect(page).toHaveURL(`/songs/${SIXTEEN_TONS_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Sixteen Tons' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Авторы' }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Merle Travis' }).first(),
  ).toHaveAttribute('href', `/performers/${MERLE_TRAVIS_ID}`);
  await expect(page.getByText(/композитор/)).toBeVisible();
  await expect(page.getByText(/автор слов/)).toBeVisible();

  await page.goto(`/songs/${ONE_O_CLOCK_JUMP_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: "One O'Clock Jump" }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Count Basie' })).toHaveAttribute(
    'href',
    `/performers/${COUNT_BASIE_ID}`,
  );
  await expect(
    page.getByRole('heading', { name: 'Текст' }),
  ).not.toBeVisible();
});
