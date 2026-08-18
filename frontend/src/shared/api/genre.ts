import type { components } from '@/api/schema';

import { getApiBaseUrl } from './base-url';

export type GenreOverview = components['schemas']['GenreOverviewResponse'];
export type GenreRelations = components['schemas']['GenreRelationsResponse'];
export type GenreSources = components['schemas']['GenreSourcesResponse'];

export type ProjectionOk<T> = { status: 'ok'; data: T };
export type ProjectionNotFound = { status: 'not_found' };
export type ProjectionError = { status: 'error'; message: string };
export type ProjectionResult<T> =
  ProjectionOk<T> | ProjectionNotFound | ProjectionError;

export type GenrePageProjections = {
  overview: ProjectionResult<GenreOverview>;
  relations: ProjectionResult<GenreRelations>;
  sources: ProjectionResult<GenreSources>;
};

const FETCH_TIMEOUT_MS = 10_000;

async function fetchProjection<T>(path: string): Promise<ProjectionResult<T>> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    });
  } catch {
    return {
      status: 'error',
      message: 'Не удалось загрузить материал.',
    };
  }

  if (response.status === 404) {
    return { status: 'not_found' };
  }

  if (!response.ok) {
    return {
      status: 'error',
      message: 'Не удалось загрузить материал.',
    };
  }

  try {
    return { status: 'ok', data: (await response.json()) as T };
  } catch {
    return {
      status: 'error',
      message: 'Не удалось загрузить материал.',
    };
  }
}

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
