import type { components } from '@/api/schema';

type TemporalBound = components['schemas']['TemporalBound'];

export function formatPersonDate(bound: TemporalBound): string {
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

export function safeExternalHref(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
      return parsed.href;
    }
    return null;
  } catch {
    return null;
  }
}
