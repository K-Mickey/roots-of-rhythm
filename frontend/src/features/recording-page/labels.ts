import type { components } from '@/api/schema';

type RecordingWorkUsageKind =
  components['schemas']['RecordingWorkView']['usage_kind'];
type OriginBadge =
  components['schemas']['RecordingOverviewResponse']['origin_badges'][number];
type LyricsVersion = components['schemas']['RecordingLyricsVersionView'];

export function formatRecordingWorkUsageKind(
  usageKind: RecordingWorkUsageKind,
): string | null {
  switch (usageKind) {
    case 'complete':
      return null;
    case 'partial':
      return 'фрагмент';
    case 'medley_component':
      return 'медли';
    default: {
      const unexpected: never = usageKind;
      throw new Error(
        `Unknown recording work usage kind: ${String(unexpected)}`,
      );
    }
  }
}

export function formatOriginBadge(value: OriginBadge): string {
  switch (value) {
    case 'first_known_performance_of':
      return 'Первое известное исполнение';
    case 'first_recording_of':
      return 'Первая известная запись';
    case 'first_released_recording_of':
      return 'Первая выпущенная запись';
    case 'recorded_by_work_author':
      return 'Записано автором произведения';
    default: {
      const unexpected: never = value;
      throw new Error(`Unknown recording origin badge: ${String(unexpected)}`);
    }
  }
}

export function formatLyricsVersionLabel(
  version: Pick<LyricsVersion, 'language_tag' | 'label' | 'creation_method'>,
): string {
  return [
    version.language_tag,
    version.label,
    version.creation_method === 'machine_translation'
      ? 'машинный перевод'
      : null,
  ]
    .filter(Boolean)
    .join(' · ');
}

export function formatLyricsVersionShortLabels(
  versions: Pick<LyricsVersion, 'language_tag'>[],
): string[] {
  const totals = new Map<string, number>();
  const positions = new Map<string, number>();
  for (const version of versions) {
    const language = version.language_tag.toUpperCase();
    totals.set(language, (totals.get(language) ?? 0) + 1);
  }
  return versions.map((version) => {
    const language = version.language_tag.toUpperCase();
    const position = (positions.get(language) ?? 0) + 1;
    positions.set(language, position);
    return totals.get(language) === 1 ? language : `${language} ${position}`;
  });
}

export function resolveSelectedLyricsVersionId(
  versions: Pick<LyricsVersion, 'id'>[],
  requestedId: string | null,
): string | null {
  return requestedId !== null &&
    versions.some((version) => version.id === requestedId)
    ? requestedId
    : (versions[0]?.id ?? null);
}
