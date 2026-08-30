import { expect, test } from '@playwright/test';

const MERLE_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000001';
const FORD_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000002';
const FORD_ID = '01a01a72-3b01-7000-8000-000000000005';
const SIXTEEN_TONS_ID = '01a01a72-3c01-7000-8000-000000000001';
const COUNTRY_ID = '01a0147a-8508-74b7-9689-e7cd00000001';
const UNKNOWN_ID = '00000000-0000-0000-0000-000000000000';
const MARIAN_RECORDING_ID = '01a01a72-5a01-7000-8000-000000000011';
const SPIRITUAL_ENGLISH_ID = '01a01a72-5a01-7000-8000-000000000003';
const SPIRITUAL_RUSSIAN_ID = '01a01a72-5a01-7000-8000-000000000004';
test('recording detail exposes credits, lyrics, origin evidence, guide, and not-found', async ({
  page,
}) => {
  await page.goto(`/recordings/${FORD_RECORDING_ID}`);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Sixteen Tons',
  );
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
  await expect(
    page.getByRole('link', { name: 'Tennessee Ernie Ford' }),
  ).toHaveAttribute('href', `/performers/${FORD_ID}`);
  await expect(page.getByRole('link', { name: 'Country' })).toHaveAttribute(
    'href',
    `/genres/${COUNTRY_ID}`,
  );
  await expect(
    page.getByRole('link', { name: 'Sixteen Tons' }),
  ).toHaveAttribute('href', `/songs/${SIXTEEN_TONS_ID}`);
  await expect(page.getByRole('tab', { name: /en · English/ })).toBeVisible();
  await expect(
    page.getByRole('tab', { name: /ru · Русский перевод/ }),
  ).toBeVisible();
  await expect(page.getByText('Машинный перевод')).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'На что обратить внимание' }),
  ).toBeVisible();
  await expect(page.getByText('Щелчки пальцами и пульс')).toBeVisible();

  await page.goto(`/recordings/${MERLE_RECORDING_ID}`);
  await expect(page.getByText('Первая известная запись')).toBeVisible();
  await expect(page.getByText('Оригинал', { exact: true })).not.toBeVisible();

  await page.goto(`/recordings/${MARIAN_RECORDING_ID}`);
  await expect(page).toHaveURL(new RegExp(`text=${SPIRITUAL_ENGLISH_ID}`));
  await expect(
    page.getByText(/Nobody knows the trouble I've seen/),
  ).toBeVisible();
  await page.getByRole('tab', { name: /ru · Русский перевод/ }).click();
  await expect(page).toHaveURL(new RegExp(`text=${SPIRITUAL_RUSSIAN_ID}`));
  await expect(page.getByText(/Никто не знает бед/)).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`text=${SPIRITUAL_ENGLISH_ID}`));

  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth,
    ),
  ).toBe(false);

  await page.goto(`/recordings/${UNKNOWN_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Запись не найдена' }),
  ).toBeVisible();
});
