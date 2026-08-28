import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type RecordingOverview =
  components['schemas']['RecordingOverviewResponse'];

export function fetchRecordingOverview(
  id: string,
): Promise<ProjectionResult<RecordingOverview>> {
  return fetchProjection<RecordingOverview>(
    `/api/v1/recordings/${encodeURIComponent(id)}`,
  );
}
