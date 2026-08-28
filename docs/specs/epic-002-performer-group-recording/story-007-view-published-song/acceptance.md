# STORY-007 приёмка TASK-007

Статус: `draft`

Владелец: Product Owner.

Story: [STORY-007](README.md).  
Task: [TASK-007](tasks.md#task-007-приёмка-story-007).  
Tracker: story [#33](https://github.com/K-Mickey/roots-of-rhythm/issues/33), task [#48](https://github.com/K-Mickey/roots-of-rhythm/issues/48).

Дата прогона: 2026-08-28. База кода: `fec7ae6` (UI TASK-006) плюс локальные правки `ruff format` и mypy-аннотаций в backend tests перед фиксацией этого документа.

## Команды и результаты

Стек: `make up`, `make migrate`, `make seed` (дважды). Health: backend `/health/ready` `ok`, frontend `/api/health` `ok`.

| Проверка | Результат |
|---|---|
| `make format-check` | pass (после `ruff format` в backend story/tests) |
| `make lint` | pass |
| `make typecheck` | pass (после аннотаций в `test_song_overview.py`, `test_lyrics_version_projection_service.py`) |
| backend unit | 166 passed, 27 deselected |
| Vitest | 36 passed (16 files) |
| backend integration | 27 passed, 166 deselected |
| `make contract-check` | pass (OpenAPI `0.7.0`; Redocly `operation-4xx-response` / `info-license` warnings) |
| Playwright | 10 passed (включая `e2e/song-catalog.spec.ts`) |
| `make seed` (повтор) | pass, идемпотентно (`Seed completed` без дублирования) |

Ручная проверка API и SSR:

- `GET /api/v1/songs` — 6 seed works, сортировка по canonical title;
- `GET /api/v1/songs/01a01a72-3c01-7000-8000-000000000001` — Sixteen Tons, credits Merle Travis (composer, lyricist), `lyrics_versions: []`;
- `GET /api/v1/songs/00000000-0000-0000-0000-000000000000` — 404 `SONG_NOT_FOUND`, «Материал не найден.»;
- SSR `/songs` — `h1` «Песни», `href` на seed song ids;
- SSR `/` — нет `href` на `/songs/{id}`;
- SSR `/songs/00000000-0000-0000-0000-000000000000` — RSC payload с `h1` «Материал не найден» (после hydration).

Проверка diff: секретов и `.env` в изменениях STORY-007 нет.

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | Playwright `song-catalog.spec.ts`; `test_song_list_http_returns_200_shape`; SSR `/songs` ссылка `Sixteen Tons` → seed id |
| AC-2 | pass | Playwright: header «Песни» → `/songs`; `SiteHeader.test.tsx` |
| AC-3 | pass | `SongPageContent.test.tsx`: нет секций «Записи» и «Послушать»; e2e One O'Clock Jump без «Текст» |
| AC-4 | pass | SSR `curl /`: нет `/songs/` detail links |
| AC-5 | pass | `test_song_overview_http_*_not_found`; `not-found.tsx`; API/SSR 404 для unknown id |
| AC-6 | pass | `SongPageContent.test.tsx` empty overview; `test_musical_work_publish_with_title_and_provenance_only`; e2e work без секции «Текст» |
| AC-7 | pass (tests) | `SongPageContent.test.tsx` + `test_song_overview_returns_public_fields_*` + `test_song_overview_related_works_include_only_outbound_source_relations`; seed **не** содержит `related_works` |
| AC-8 | pass (tests) | `SongPageContent.test.tsx` unavailable body; `test_lyrics_version_projection_service` withheld body; seed **без** `lyrics_versions` |
| AC-9 | pass (tests) | `labels.test.ts`; tab label «машинный перевод» в `SongPageContent.test.tsx`; seed без machine translation |

## NFR

- `NFR-001`: каталог и overview рендерятся через RSC (`fetchProjection`); имена и `href` в SSR HTML `/songs`.
- `NFR-002`: list/get API без auth и ES; плеер не добавлен.
- `NFR-003`: UI не ограничивает число credits, classifications, related works или lyrics tabs фиксированным maximum.
- `NFR-004`: страница песни не запрашивает Recording endpoints и не показывает recording UI.

## Out of scope (подтверждено)

Recording persistence/pages, жанровые фасеты исполнений, origin Claims, плеер, Session/Take/Master, Editorial UI, глобальная локализация интерфейса.

## Известные ограничения

- Controlled seed: six MusicalWork с WorkCredit, но **без** `lyrics_versions` и **без** `related_works`; AC-7/8/9 на corpus подтверждены unit/backend tests, не e2e на seed.
- Все seeded works имеют composer credit; AC-6 «без credits» — через unit/domain tests, не через seed work.
- Redocly `operation-4xx-response` для `GET /api/v1/songs` и `info-license` warning (как в STORY-001–005).
- Прогон требует `make migrate` перед первым `make seed` на volume без `musical_works`.

## Tracker

Story [#33](https://github.com/K-Mickey/roots-of-rhythm/issues/33) и task [#48](https://github.com/K-Mickey/roots-of-rhythm/issues/48) **не закрыты** — статус `draft` до утверждения Product Owner.

## История

- 2026-08-28: первый прогон приёмки STORY-007 TASK-007 (статус `draft`).
