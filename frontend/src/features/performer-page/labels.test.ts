import { describe, expect, it } from 'vitest';

import { formatPersonDate, safeExternalHref } from './labels';

describe('formatPersonDate', () => {
  it('formats every temporal precision', () => {
    expect(formatPersonDate({ year: 1920, precision: 'exact_year' })).toBe(
      '1920',
    );
    expect(formatPersonDate({ year: 1920, precision: 'circa_year' })).toBe(
      'ок. 1920',
    );
    expect(formatPersonDate({ year: 1920, precision: 'decade' })).toBe(
      '1920-е',
    );
    expect(formatPersonDate({ year: 1920, precision: 'early_decade' })).toBe(
      'начало 1920-х',
    );
    expect(formatPersonDate({ year: 1920, precision: 'mid_decade' })).toBe(
      'середина 1920-х',
    );
    expect(formatPersonDate({ year: 1920, precision: 'late_decade' })).toBe(
      'конец 1920-х',
    );
  });
});

describe('safeExternalHref', () => {
  it('keeps http(s) URLs and rejects other schemes', () => {
    expect(safeExternalHref('https://example.com/a')).toBe(
      'https://example.com/a',
    );
    expect(safeExternalHref('http://example.com/a')).toBe(
      'http://example.com/a',
    );
    expect(safeExternalHref('javascript:alert(1)')).toBeNull();
    expect(safeExternalHref('ftp://example.com/a')).toBeNull();
    expect(safeExternalHref('not a url')).toBeNull();
  });
});
