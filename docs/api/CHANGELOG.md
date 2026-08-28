# API changelog

## 0.8.0 — 2026-08-28

STORY-008 published Recording overview:

- added `GET /api/v1/recordings/{recording_id}` with published Works, visible credits, Genres, rights-aware lyrics and optional ListeningGuide;
- non-public Recording and Recording without a published primary Person/Group return `RECORDING_NOT_FOUND`;
- `first_release_date` is `null` until STORY-009 and `origin_badges` is empty until TASK-005.

Breaking changes: none; additive.

## 0.7.0 — 2026-08-28

STORY-007 published Song catalog and overview:

- added `GET /api/v1/songs` returning `SongListResponse` with `items` of `SongSummary` (`id`, `name`);
- added `GET /api/v1/songs/{song_id}` returning `SongOverviewResponse` with credits, classifications, related Works and rights-aware `lyrics_versions`;
- `period` is `{ start, end }` with nullable `TemporalBound`; `external_identities` reuse `ExternalIdentityView`;
- `credits` are `{ person: { id, name }, role, credited_as }`; `classifications` are published Genre summaries;
- `related_works` are `{ relation_type, work: { id, name } }`; lyrics views include optional `body` and `body_unavailable_reason`;
- unknown or non-public identifiers return `SONG_NOT_FOUND` with the same safe message as Genre;
- list failures use `INTERNAL_ERROR` and do not use `SONG_NOT_FOUND`.

Breaking changes: none; additive.

## 0.6.0 — 2026-08-20

STORY-006 published Group catalog and overview:

- added `GET /api/v1/groups` returning `GroupListResponse` with `items` of `GroupSummary` (`id`, `name`);
- added `GET /api/v1/groups/{group_id}` returning `GroupOverviewResponse` (`id`, `name`, `aliases`, `description`, `period`, `primary_image`, `genres`, `members`);
- `period` is `{ start, end }` with nullable `TemporalBound`;
- `members` are `{ id, name, period, roles_or_instruments }` for published memberships of published Performers;
- unknown or non-public identifiers return `GROUP_NOT_FOUND` with the same safe message as Genre;
- list failures use `INTERNAL_ERROR` and do not use `GROUP_NOT_FOUND`.

Breaking changes: none; additive.

## 0.5.0 — 2026-08-19

STORY-005 public Performer overview content:

- extended `PerformerOverviewResponse` with `aliases`, `birth_date`, `death_date` and `external_identities`;
- dates reuse `TemporalBound` (`year` plus `exact_year | circa_year | decade | early_decade | mid_decade | late_decade`) and are nullable;
- `external_identities` items are `{ provider, identifier, url }` with nullable `url`;
- `GET /api/v1/performers` remains `{ id, name }` summaries; overview still omits editorial status, deleted flags and timestamps;
- `primary_image` stays nullable and is `null` in this slice.

Breaking changes: none; additive.

## 0.4.0 — 2026-08-19

STORY-005 published Performer catalog and overview:

- added `GET /api/v1/performers` returning `PerformerListResponse` with `items` of `PerformerSummary` (`id`, `name`);
- added `GET /api/v1/performers/{performer_id}` returning `PerformerOverviewResponse` (`id`, `name`, optional `biography`, `primary_image`, `genres`);
- listed and returned only published, not deleted Person; empty catalog is `200` with `items: []`;
- unknown or non-public identifiers return `PERFORMER_NOT_FOUND` with the same safe message as Genre;
- list failures use `INTERNAL_ERROR` and do not use `PERFORMER_NOT_FOUND`.

Breaking changes: none; additive.

## 0.3.0 — 2026-08-19

STORY-004 published Genre catalog:

- added `GET /api/v1/genres` returning `GenreListResponse` with `items` of `GenreSummary` (`id`, `name`);
- listed only published, not deleted Genres, ordered by canonical name;
- empty corpus returns `200` with `items: []`;
- retained `INTERNAL_ERROR` for read failures; this operation does not use `GENRE_NOT_FOUND`.

Breaking changes: none; additive.

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
