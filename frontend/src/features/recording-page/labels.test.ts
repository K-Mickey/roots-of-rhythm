import { expect, it } from 'vitest';

import { formatOriginBadge } from './labels';

it('formats every supported Recording origin badge precisely', () => {
  expect(formatOriginBadge('first_known_performance_of')).toBe(
    'Первое известное исполнение',
  );
  expect(formatOriginBadge('first_recording_of')).toBe(
    'Первая известная запись',
  );
  expect(formatOriginBadge('first_released_recording_of')).toBe(
    'Первая выпущенная запись',
  );
  expect(formatOriginBadge('recorded_by_work_author')).toBe(
    'Записано автором произведения',
  );
});
