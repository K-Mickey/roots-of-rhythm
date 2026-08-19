# STORY-001 приёмка TASK-009

Статус: `accepted`

Владелец: Product Owner.

Story: [STORY-001](README.md).  
Task: [TASK-009](tasks.md#task-009-выполнить-итоговую-приёмку-vertical-slice).  
Tracker: [#17](https://github.com/K-Mickey/roots-of-rhythm/issues/17).

Дата прогона: 2026-08-19. Коммит кода vertical slice на момент прогона: `e85677a` (плюс локальная правка unused `type: ignore` в `test_genre_sources.py`, если ещё не закоммичена).

## Команды и результаты

Стек: `docker compose up -d --build --wait`, затем `make seed`. Health: backend `/health/ready` `ok`, frontend `/api/health` `ok`.

| Проверка | Результат |
|---|---|
| `uv run ruff format --check` / `ruff check` | pass |
| `uv run mypy` | pass после удаления unused `type: ignore[return-value]` в `tests/discovery/application/test_genre_sources.py` |
| backend unit (`pytest -m "not integration"`) | 69 passed |
| backend integration (`pytest -m integration`) | 9 passed |
| frontend Prettier / ESLint / `tsc` | pass |
| Vitest | 11 passed |
| OpenAPI Redocly | valid; 1 warning `info-license` (не блокирует) |
| `openapi-typescript` drift | pass (diff empty) |
| Compose production images | built; containers healthy |
| Playwright (`scaffold` + Swing page) | 2 passed против `127.0.0.1:3000` / `:8000` |

Host `make setup` в этой среде не нашёл `pnpm` в PATH; frontend checks запускались через `frontend/node_modules/.bin`. На машине с Corepack/`pnpm` 11.19 каноничны команды из [development.md](../../../development.md).

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | Playwright Swing: `h1` Swing, definition в SSR HTML; seed overview API возвращает name/definition. Заполненные секции seed: relations + sources. |
| AC-2 | pass | Seed Swing: `primary_image`, `period`, `geography_or_origin`, `historical_context`, `formation`, `characteristic_features` пусты. HTML не содержит headings «Исторический контекст» / «Характерные черты». Vitest `omits empty optional sections`. |
| AC-3 | pass | API: `developed_from` Jazz и `contributed_to_emergence_of` Jump Blues, explanation, temporal/geographic labels, `supported`. UI: «Развился из — Jazz», «Участвовал в формировании — Jump Blues». |
| AC-4 | pass | Обе seed relations `supported` с reviewed references (по 2). Domain/application: publish `supported` без reviewed support отклоняется (`test_publish_requires_completeness_and_evidence_rules`, `test_publish_requires_published_endpoints_and_reviewed_support`). |
| AC-5 | pass | Domain draft default `unverified`; UI label «Пока не подтверждено источниками» (`labels.test.ts`). Seed не содержит unverified public relation — критерий закрыт тестами статусов, не live seed page. |
| AC-6 | pass | Live seed не содержит `disputed`. Unit: `test_relations_query_maps_disputed_reviewed_evidence`; publish без `opposes` отклоняется. UI label «Есть существенные разногласия». |
| AC-7 | pass | Live seed не содержит `overlaps_with`. Domain: `test_overlaps_with_uses_canonical_id_order`. UI symmetric label «Пересекается с». На Jazz page обратная directed relation показана как «Дальнейшее развитие — Swing» без второй строки в БД. |
| AC-8 | pass | HTML Swing/Jazz: имя связанного Genre не обёрнуто в `<a href="/genres/...">`. |
| AC-9 | pass | `GET .../genres/00000000-0000-0000-0000-000000000000` → 404 `GENRE_NOT_FOUND`. DRAFT/ARCHIVED Genre скрыты unit-тестами overview/relations/sources. Draft claim не public (`get_publicly_visible`). |
| AC-10 | pass | `make seed` идемпотентно: Jazz, Swing, Jump Blues. Seed явно не создаёт Performer/Group/Recording. |
| AC-11 | pass | Два published Claims + reviewed Evidence Smithsonian / Library of Congress; sources titles `Jazz`, `Rhythm and Blues`. |
| AC-12 | pass | `test_draft_requires_only_distinct_endpoints_and_type`; create_draft в application/persistence tests; public list не включает draft. |
| AC-13 | pass | `ClaimPublicationError` с `missing_fields` при неполном publish (`test_publish_requires_completeness_and_evidence_rules`). |
| AC-14 | pass | Три operations; frontend `fetchGenrePage` — три параллельных fetch. Integration sources: bounded SELECT count (без per-source N+1). |
| AC-15 | pass | Vitest: overview остаётся при error relations/sources; inline «Повторить». UI contract + `SectionError` `h2`. Live 500 секций в этом прогоне не инжектился. |

## Out of scope (подтверждено отсутствием в runtime)

В `compose.yaml`, lockfiles приложения и `backend/src` / `frontend/src` нет: i18n/locale stack, Performer/Group/Recording pages, Elasticsearch, Redis, graph DB, очередей, authentication/Keycloak, Caddy, Sentry/Grafana.

Исследования Caddy/Sentry остаются в `docs/research/` и `EPIC-012` и не входят в Compose STORY-001.

## Известные ограничения

- Visual review узкий/широкий viewport на трёх seed pages не прилагается скриншотами; калибровка spacing — TASK-008, не формальный screenshot pack.
- Seed не покрывает live UI для `unverified`, `disputed`, `overlaps_with`; эти AC закрыты unit/application tests + labels.
- Между тремя reads нет общего snapshot (как в story).
- Redocly warning `info-license`.
- `frontend/AGENTS.md` создаётся `next dev` (Next.js 16); не является продуктовым scope.

## Tracker

Issue TASK-009: [#17](https://github.com/K-Mickey/roots-of-rhythm/issues/17) — закрыт.  
Story: [#22](https://github.com/K-Mickey/roots-of-rhythm/issues/22).

## История

- 2026-08-19: первый прогон приёмки STORY-001.
- 2026-08-19: Product Owner принял прогон с зафиксированными ограничениями; статус `accepted`.
