# API changelog

## 0.2.0 — 2026-08-17

STORY-001 page projections split by Product Owner decision:

- changed `GET /api/v1/genres/{genre_id}` to return `GenreOverviewResponse` without relations and Sources;
- added `GET /api/v1/genres/{genre_id}/relations` returning one bounded `GenreRelationsResponse`;
- added `GET /api/v1/genres/{genre_id}/sources` returning a deduplicated `GenreSourcesResponse`;
- retained the same public visibility and `GENRE_NOT_FOUND` behavior for all three operations;
- changed failure semantics: overview failure remains a page error, while relations and Sources failures are independent section errors.

Breaking changes: `GenrePageResponse` was removed and the existing Genre operation changed response shape. The three operations are implemented by the STORY-001 public API and SSR Genre page; URL version remains `/api/v1` as the first unreleased API generation.

## 0.1.0 — 2026-08-16

Initial public contract for STORY-001:

- added `GET /api/v1/genres/{genre_id}`;
- added atomic `GenrePageResponse` with optional Genre sections, relations and Sources;
- added approximate temporal and text-first geographic contexts;
- added evidence statuses, roles and public Source references;
- added `GENRE_NOT_FOUND` and `INTERNAL_ERROR` responses.

Breaking changes: none; this is the first public API version.
