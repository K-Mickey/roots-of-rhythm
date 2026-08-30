import type { components } from '@/api/schema';

type TemporalBound = components['schemas']['TemporalBound'];
type SongPeriodView = components['schemas']['SongPeriodView'];
type WorkCreditRole = components['schemas']['WorkCreditRole'];
type WorkRelationType = components['schemas']['WorkRelationType'];

export function formatTemporalBound(bound: TemporalBound): string {
  const { year, precision } = bound;
  switch (precision) {
    case 'exact_year':
      return String(year);
    case 'circa_year':
      return `ок. ${year}`;
    case 'decade':
      return `${year}-е`;
    case 'early_decade':
      return `начало ${year}-х`;
    case 'mid_decade':
      return `середина ${year}-х`;
    case 'late_decade':
      return `конец ${year}-х`;
    default: {
      const unexpected: never = precision;
      throw new Error(`Unknown temporal precision: ${String(unexpected)}`);
    }
  }
}

export function formatPeriod(period: SongPeriodView): string | null {
  const parts: string[] = [];
  if (period.start !== null) {
    parts.push(formatTemporalBound(period.start));
  }
  if (period.end !== null) {
    parts.push(formatTemporalBound(period.end));
  }
  return parts.length > 0 ? parts.join(' — ') : null;
}

export function hasPeriodBounds(period: SongPeriodView): boolean {
  return period.start !== null || period.end !== null;
}

export function formatWorkCreditRole(role: WorkCreditRole): string {
  switch (role) {
    case 'composer':
      return 'композитор';
    case 'lyricist':
      return 'автор слов';
    case 'writer':
      return 'автор';
    case 'translator':
      return 'переводчик';
    case 'adapter':
      return 'адаптор';
    case 'arranger':
      return 'аражировщик';
    case 'other':
      return 'другое';
    default: {
      const unexpected: never = role;
      throw new Error(`Unknown work credit role: ${String(unexpected)}`);
    }
  }
}

export function formatWorkRelationType(relationType: WorkRelationType): string {
  switch (relationType) {
    case 'translation_of':
      return 'перевод';
    case 'adaptation_of':
      return 'адаптация';
    case 'arrangement_of':
      return 'аранжировка';
    case 'medley_of':
      return 'медли';
    default: {
      const unexpected: never = relationType;
      throw new Error(`Unknown work relation type: ${String(unexpected)}`);
    }
  }
}

export function safeExternalHref(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
      return parsed.toString();
    }
    return null;
  } catch {
    return null;
  }
}
