import { describe, expect, it } from 'vitest';

import {
  formatPeriod,
  formatWorkCreditRole,
  formatWorkRelationType,
} from './labels';
import {
  formatLyricsVersionLabel,
  formatLyricsVersionShortLabels,
  resolveSelectedLyricsVersionId,
} from '../recording-page/labels';

describe('song page labels', () => {
  it('formats temporal bounds by precision', () => {
    expect(
      formatPeriod({
        start: { year: 1935, precision: 'exact_year' },
        end: { year: 1950, precision: 'circa_year' },
      }),
    ).toBe('1935 — ок. 1950');
  });

  it('maps work credit roles', () => {
    expect(formatWorkCreditRole('composer')).toBe('композитор');
    expect(formatWorkCreditRole('lyricist')).toBe('автор слов');
    expect(formatWorkCreditRole('arranger')).toBe('аражировщик');
  });

  it('maps work relation types', () => {
    expect(formatWorkRelationType('translation_of')).toBe('перевод');
    expect(formatWorkRelationType('arrangement_of')).toBe('аранжировка');
  });

  it('builds lyrics tab labels with machine translation marker', () => {
    expect(
      formatLyricsVersionLabel({
        language_tag: 'en',
        label: 'Original',
        creation_method: 'original',
      }),
    ).toBe('en · Original');

    expect(
      formatLyricsVersionLabel({
        language_tag: 'ru',
        label: null,
        creation_method: 'machine_translation',
      }),
    ).toBe('ru · машинный перевод');
  });

  it('uses short uppercase labels and numbers duplicate languages', () => {
    expect(
      formatLyricsVersionShortLabels([
        { language_tag: 'en' },
        { language_tag: 'ru' },
        { language_tag: 'en' },
        { language_tag: 'fr' },
      ]),
    ).toEqual(['EN 1', 'RU', 'EN 2', 'FR']);
  });

  it('resolves selected lyrics version from query param', () => {
    const versions = [{ id: 'lyrics-1' }, { id: 'lyrics-2' }];

    expect(resolveSelectedLyricsVersionId(versions, 'lyrics-2')).toBe(
      'lyrics-2',
    );
    expect(resolveSelectedLyricsVersionId(versions, 'invalid')).toBe(
      'lyrics-1',
    );
    expect(resolveSelectedLyricsVersionId(versions, null)).toBe('lyrics-1');
    expect(resolveSelectedLyricsVersionId([], 'lyrics-1')).toBeNull();
  });
});
