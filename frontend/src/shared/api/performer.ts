import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type PerformerList = components['schemas']['PerformerListResponse'];

export type PerformerOverview =
  components['schemas']['PerformerOverviewResponse'];

export function fetchPublishedPerformers(): Promise<
  ProjectionResult<PerformerList>
> {
  return fetchProjection<PerformerList>('/api/v1/performers');
}

export function fetchPerformerOverview(
  performerId: string,
): Promise<ProjectionResult<PerformerOverview>> {
  return fetchProjection<PerformerOverview>(
    `/api/v1/performers/${encodeURIComponent(performerId)}`,
  );
}
