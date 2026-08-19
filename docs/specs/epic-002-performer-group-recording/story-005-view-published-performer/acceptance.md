# STORY-005 приёмка

Статус: `accepted`

Владелец: Product Owner.

Story: [STORY-005](README.md).  
Декомпозиция: [tasks.md](tasks.md).  
Tracker: [#31](https://github.com/K-Mickey/roots-of-rhythm/issues/31).

Дата прогона: 2026-08-20. База кода: `59cf017` (main).

## Команды и результаты

Стек: `docker compose up -d --wait`, `make seed`. Health: backend `/health/ready` `ok`, frontend `/api/health` `ok`.

| Проверка | Результат |
|---|---|
| `make format-check` | pass (после ruff format) |
| `make lint` | pass |
| `make typecheck` | pass |
| backend unit | 103 passed, 13 deselected |
| backend integration | 13 passed |
| `make contract-check` | pass (OpenAPI `0.5.0`) |
| Vitest | не прогнан: timeout старта forks worker в этой среде |
| Playwright (`performer-*.spec.ts`) | не прогнан: Chromium не установлен (`pnpm exec playwright install`) |

Ручная проверка API и SSR:

- `GET /api/v1/performers` — 6 seed-исполнителей, сортировка по имени;
- `GET /api/v1/performers/{armstrong_id}` — `genres`: Jazz, Swing;
- `GET /api/v1/performers/00000000-…` — 404;
- SSR `/performers` — `href` на seed id;
- SSR `/` — нет `/performers/{id}`;
- SSR `/performers/00000000-…` — «Материал не найден».

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | SSR `/performers`: заголовок каталога и ссылки на seed performers |
| AC-2 | pass | API overview Louis Armstrong; seed corpus в integration `test_corpus_seed` |
| AC-3 | pass | SSR header: ссылка «Исполнители» → `/performers` |
| AC-4 | pass | SSR `/`: нет detail-ссылок `/performers/{id}` |
| AC-5 | pass | API 404; SSR not-found «Материал не найден» |
| AC-6 | pass | unit `test_performers.py`, integration entrypoints |
| AC-7 | pass | unit `test_performer_overview.py`; UI скрывает пустые секции |
| AC-8 | pass | unit `test_assignments.py`; integration assignment publish |

## NFR

- `NFR-001`: имена каталога в SSR HTML (`href` без обязательного page JS).
- `NFR-002`: list/get API без auth, ES, очереди, графа.
- `NFR-003`: без поиска, slug, Editorial UI, плеера.

## Out of scope (подтверждено)

Group/Recording/Work/Release pages; related на Genre (STORY-010); MediaAsset upload; provenance/evidence UI assignment.

## Известные ограничения

- Vitest и Playwright для performer e2e не подтверждены в этом прогоне из-за окружения; backend и contract-check зелёные.
- Redocly `info-license` warning (как в STORY-001–003).

## Tracker

Story: [#31](https://github.com/K-Mickey/roots-of-rhythm/issues/31) — закрыт.

## История

- 2026-08-20: первый прогон приёмки STORY-005 (статус `accepted`).
