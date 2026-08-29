import type { components } from '@/api/schema';

type RecordingWorkUsageKind =
  components['schemas']['RecordingWorkView']['usage_kind'];
type OriginBadge =
  components['schemas']['RecordingOverviewResponse']['origin_badges'][number];

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
