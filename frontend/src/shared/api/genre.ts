import type { components } from '@/api/schema';

import { fetchProjection, type ProjectionResult } from './projection';

export type {
  ProjectionError,
  ProjectionNotFound,
  ProjectionOk,
  ProjectionResult,
} from './projection';

export type GenreList = components['schemas']['GenreListResponse'];
export type GenreOverview = components['schemas']['GenreOverviewResponse'];
export type GenreRelations = components['schemas']['GenreRelationsResponse'];
export type GenreSources = components['schemas']['GenreSourcesResponse'];

export type GenrePageProjections = {
  overview: ProjectionResult<GenreOverview>;
  relations: ProjectionResult<GenreRelations>;
  sources: ProjectionResult<GenreSources>;
};

export async function fetchGenrePage(
  genreId: string,
): Promise<GenrePageProjections> {
  const encodedId = encodeURIComponent(genreId);
  const [overview, relations, sources] = await Promise.all([
    fetchProjection<GenreOverview>(`/api/v1/genres/${encodedId}`),
    fetchProjection<GenreRelations>(`/api/v1/genres/${encodedId}/relations`),
    fetchProjection<GenreSources>(`/api/v1/genres/${encodedId}/sources`),
  ]);

  return { overview, relations, sources };
}

export async function fetchPublishedGenres(): Promise<
  ProjectionResult<GenreList>
> {
  return fetchProjection<GenreList>('/api/v1/genres');
}
