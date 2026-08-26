import type { components } from '@/api/schema';

type TemporalBound = components['schemas']['TemporalBound'];
type GroupPeriodView = components['schemas']['GroupPeriodView'];

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

export function formatPeriod(period: GroupPeriodView): string | null {
  const parts: string[] = [];
  if (period.start !== null) {
    parts.push(formatTemporalBound(period.start));
  }
  if (period.end !== null) {
    parts.push(formatTemporalBound(period.end));
  }
  return parts.length > 0 ? parts.join(' — ') : null;
}

export function hasPeriodBounds(period: GroupPeriodView): boolean {
  return period.start !== null || period.end !== null;
}
