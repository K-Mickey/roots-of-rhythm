import { describe, expect, it } from 'vitest';

import { formatPeriod, formatTemporalBound } from './labels';

describe('group page labels', () => {
  it('formats temporal bounds by precision', () => {
    expect(formatTemporalBound({ year: 1935, precision: 'exact_year' })).toBe(
      '1935',
    );
    expect(formatTemporalBound({ year: 1950, precision: 'circa_year' })).toBe(
      'ок. 1950',
    );
  });

  it('joins period bounds when present', () => {
    expect(
      formatPeriod({
        start: { year: 1935, precision: 'exact_year' },
        end: { year: 1950, precision: 'circa_year' },
      }),
    ).toBe('1935 — ок. 1950');
    expect(formatPeriod({ start: null, end: null })).toBeNull();
  });
});
