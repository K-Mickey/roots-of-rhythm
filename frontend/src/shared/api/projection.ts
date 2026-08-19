import { getApiBaseUrl } from './base-url';

export type ProjectionOk<T> = { status: 'ok'; data: T };
export type ProjectionNotFound = { status: 'not_found' };
export type ProjectionError = { status: 'error'; message: string };
export type ProjectionResult<T> =
  ProjectionOk<T> | ProjectionNotFound | ProjectionError;

const FETCH_TIMEOUT_MS = 10_000;

export async function fetchProjection<T>(
  path: string,
): Promise<ProjectionResult<T>> {
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
