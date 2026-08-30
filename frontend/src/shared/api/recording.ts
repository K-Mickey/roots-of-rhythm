import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type RecordingList = components['schemas']['RecordingListResponse'];

export type RecordingOverview =
  components['schemas']['RecordingOverviewResponse'];

export function fetchPublishedRecordings(): Promise<
  ProjectionResult<RecordingList>
> {
  return fetchProjection<RecordingList>('/api/v1/recordings');
}

export function fetchRecordingOverview(
  id: string,
): Promise<ProjectionResult<RecordingOverview>> {
  return fetchProjection<RecordingOverview>(
    `/api/v1/recordings/${encodeURIComponent(id)}`,
  );
}
