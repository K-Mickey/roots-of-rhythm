import type { components } from '@/api/schema';

type RecordingWorkUsageKind =
  components['schemas']['RecordingWorkView']['usage_kind'];

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
      throw new Error(`Unknown recording work usage kind: ${String(unexpected)}`);
    }
  }
}
