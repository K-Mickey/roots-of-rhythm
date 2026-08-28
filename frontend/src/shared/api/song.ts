import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type SongList = components['schemas']['SongListResponse'];

export type SongOverview = components['schemas']['SongOverviewResponse'];

export function fetchPublishedSongs(): Promise<ProjectionResult<SongList>> {
  return fetchProjection<SongList>('/api/v1/songs');
}

export function fetchSongOverview(
  songId: string,
): Promise<ProjectionResult<SongOverview>> {
  return fetchProjection<SongOverview>(
    `/api/v1/songs/${encodeURIComponent(songId)}`,
  );
}
