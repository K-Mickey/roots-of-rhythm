import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type GroupList = components['schemas']['GroupListResponse'];

export type GroupOverview = components['schemas']['GroupOverviewResponse'];

export function fetchPublishedGroups(): Promise<ProjectionResult<GroupList>> {
  return fetchProjection<GroupList>('/api/v1/groups');
}

export function fetchGroupOverview(
  groupId: string,
): Promise<ProjectionResult<GroupOverview>> {
  return fetchProjection<GroupOverview>(
    `/api/v1/groups/${encodeURIComponent(groupId)}`,
  );
}
