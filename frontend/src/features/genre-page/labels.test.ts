import { describe, expect, it } from 'vitest';

import {
  evidenceStatusLabel,
  relationPerspectiveLabel,
  sourceCitationIndex,
} from './labels';

describe('genre page labels', () => {
  it('maps relation perspective labels', () => {
    expect(relationPerspectiveLabel('developed_from', 'subject')).toBe(
      'Развился из',
    );
    expect(
      relationPerspectiveLabel('contributed_to_emergence_of', 'subject'),
    ).toBe('Участвовал в формировании');
    expect(relationPerspectiveLabel('overlaps_with', 'symmetric')).toBe(
      'Пересекается с',
    );
    expect(relationPerspectiveLabel('influenced', 'target')).toBe(
      'Влияние со стороны',
    );
  });

  it('maps evidence status to text labels', () => {
    expect(evidenceStatusLabel('supported')).toBe('Подтверждено источниками');
    expect(evidenceStatusLabel('unverified')).toBe(
      'Пока не подтверждено источниками',
    );
    expect(evidenceStatusLabel('disputed')).toBe(
      'Есть существенные разногласия',
    );
  });

  it('computes 1-based citation markers from sources order', () => {
    const sources = [{ id: 'a' }, { id: 'b' }];
    expect(sourceCitationIndex('a', sources)).toBe(1);
    expect(sourceCitationIndex('b', sources)).toBe(2);
    expect(sourceCitationIndex('missing', sources)).toBeNull();
  });
});
