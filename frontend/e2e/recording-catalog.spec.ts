import { expect, test } from '@playwright/test';

const MERLE_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000001';
const FORD_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000002';
const STEVIE_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000003';
const MARIAN_RECORDING_ID = '01a01a72-5a01-7000-8000-000000000011';
const LOUIS_RECORDING_ID = '01a01a72-5a01-7000-8000-000000000012';
const MERLE_TRAVIS_ID = '01a01a72-3b01-7000-8000-000000000001';
const FORD_ID = '01a01a72-3b01-7000-8000-000000000005';
const STEVIE_WONDER_ID = '01a01a72-3b01-7000-8000-000000000006';
const COUNTRY_ID = '01a0147a-8508-74b7-9689-e7cd00000001';
const RNB_ID = '01a0147a-8508-74b7-9689-e7cd00000002';
test('recording catalog exposes public seed recordings and related links', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Записи' }).click();
  await expect(page).toHaveURL('/recordings');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Записи' }),
  ).toBeVisible();

  for (const recordingId of [
    MARIAN_RECORDING_ID,
    LOUIS_RECORDING_ID,
    MERLE_RECORDING_ID,
    FORD_RECORDING_ID,
    STEVIE_RECORDING_ID,
  ]) {
    await expect(
      page.locator(`a[href="/recordings/${recordingId}"]`),
    ).toBeVisible();
  }
  await expect(
    page.locator(`a[href="/performers/${MERLE_TRAVIS_ID}"]`),
  ).toHaveText('Merle Travis');
  await expect(page.locator(`a[href="/performers/${FORD_ID}"]`)).toHaveText(
    'Tennessee Ernie Ford',
  );
  await expect(
    page.locator(`a[href="/performers/${STEVIE_WONDER_ID}"]`),
  ).toHaveText('Stevie Wonder');
  await expect(page.locator(`a[href="/genres/${COUNTRY_ID}"]`)).toHaveCount(2);
  await expect(page.locator(`a[href="/genres/${RNB_ID}"]`)).toHaveText(
    'Rhythm and Blues',
  );

  const stevieItem = page
    .locator(`a[href="/recordings/${STEVIE_RECORDING_ID}"]`)
    .locator('xpath=ancestor::li');
  await expect(stevieItem).not.toContainText('Период записи:');
});
