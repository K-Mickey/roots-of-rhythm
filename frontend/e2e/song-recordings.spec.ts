import { expect, test } from '@playwright/test';

const SONG_ID = '01a01a72-3c01-7000-8000-000000000001';
const MERLE_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000001';
const FORD_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000002';
const STEVIE_RECORDING_ID = '01a01a72-4a01-7000-8000-000000000003';
const ENGLISH_TEXT_ID = '01a01a72-4a01-7000-8000-000000000031';
const RUSSIAN_TEXT_ID = '01a01a72-4a01-7000-8000-000000000032';
const COUNTRY_ID = '01a0147a-8508-74b7-9689-e7cd00000001';
const RNB_ID = '01a0147a-8508-74b7-9689-e7cd00000002';
test('Sixteen Tons switches recordings, facets, text, history, SSR, and mobile layout', async ({
  page,
  request,
}) => {
  const direct = await request.get(
    `/songs/${SONG_ID}?recording=${FORD_RECORDING_ID}&text=${RUSSIAN_TEXT_ID}`,
  );
  expect(direct.ok()).toBeTruthy();
  expect(await direct.text()).toContain('Щелчки пальцами и пульс');

  await page.goto(`/songs/${SONG_ID}`);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Sixteen Tons' }),
  ).toBeVisible();
  await expect(
    page.getByRole('navigation', {
      name: 'Хронология известных записей',
    }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Country (2)' })).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Rhythm and Blues (1)' }),
  ).toBeVisible();
  await expect(page.getByText('Первая известная запись').first()).toBeVisible();

  await page.evaluate(() => {
    (
      window as Window & { storyNavigationMarker?: string }
    ).storyNavigationMarker = 'preserved';
  });
  await page
    .locator(`a[href*="recording=${FORD_RECORDING_ID}"]`)
    .filter({ hasText: 'Sixteen Tons' })
    .click();
  await expect(page).toHaveURL(
    new RegExp(`recording=${FORD_RECORDING_ID}.*text=${ENGLISH_TEXT_ID}`),
  );
  expect(
    await page.evaluate(
      () =>
        (window as Window & { storyNavigationMarker?: string })
          .storyNavigationMarker,
    ),
  ).toBe('preserved');
  await expect(page.getByText('Tennessee Ernie Ford').first()).toBeVisible();
  await expect(page.getByText('Щелчки пальцами и пульс')).toBeVisible();
  const firstTab = await page.getByRole('tab').nth(0).boundingBox();
  const secondTab = await page.getByRole('tab').nth(1).boundingBox();
  expect(firstTab).not.toBeNull();
  expect(secondTab).not.toBeNull();
  expect(Math.abs(firstTab!.y - secondTab!.y)).toBeLessThan(2);

  await page
    .getByRole('tab', {
      name: 'ru · Русский перевод · машинный перевод',
    })
    .click();
  await expect(page).toHaveURL(new RegExp(`text=${RUSSIAN_TEXT_ID}`));
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`text=${ENGLISH_TEXT_ID}`));
  await page.goForward();
  await expect(page).toHaveURL(new RegExp(`text=${RUSSIAN_TEXT_ID}`));

  await page.getByRole('link', { name: 'Rhythm and Blues (1)' }).click();
  await expect(page).toHaveURL(
    new RegExp(`genre=${RNB_ID}.*recording=${STEVIE_RECORDING_ID}`),
  );
  await expect(
    page.getByRole('navigation', {
      name: 'Хронология известных записей',
    }),
  ).toContainText('Stevie Wonder');
  await page.getByRole('link', { name: 'Country (2)' }).click();
  await expect(page).toHaveURL(new RegExp(`genre=${COUNTRY_ID}`));
  await expect(
    page.getByRole('navigation', {
      name: 'Хронология известных записей',
    }),
  ).toContainText('Merle Travis');
  await expect(
    page.getByRole('navigation', {
      name: 'Хронология известных записей',
    }),
  ).toContainText('Tennessee Ernie Ford');

  const historyBeforeInvalid = await page.evaluate(() => history.length);
  await page.goto(
    `/songs/${SONG_ID}?genre=invalid&recording=invalid&text=invalid`,
  );
  await expect(page).not.toHaveURL(/invalid/);
  expect(await page.evaluate(() => history.length)).toBe(
    historyBeforeInvalid + 1,
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/songs/${SONG_ID}?recording=${MERLE_RECORDING_ID}`);
  const mobileTimeline = page.getByRole('navigation', {
    name: 'Хронология известных записей',
  });
  const mobileRecording = page.getByRole('heading', {
    level: 2,
    name: 'Sixteen Tons',
  });
  await expect(mobileTimeline).toBeVisible();
  await expect(mobileRecording).toBeVisible();
  const timelineBox = await mobileTimeline.boundingBox();
  const recordingBox = await mobileRecording.boundingBox();
  expect(timelineBox).not.toBeNull();
  expect(recordingBox).not.toBeNull();
  expect(timelineBox!.y).toBeLessThan(recordingBox!.y);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth,
    ),
  ).toBe(false);
});
