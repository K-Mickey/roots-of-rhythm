# Декомпозиция STORY-001

Статус: `accepted`.

Story: [STORY-001](README.md).  
Контракты: [UI](ui.md), [Data/API workshop](data-api-workshop.md), [OpenAPI 0.2.0](../../../api/openapi.yaml).  
Архитектура: [ADR-0004](../../../decisions/0004-application-stack.md), [структура модулей](../../../module-structure.md).

Цель декомпозиции — получить минимальные проверяемые work items первой vertical slice. Границы девяти tasks и создание новых перечисленных tests, fixtures и test configuration утверждены Product Owner 2026-08-17. До начала кода всё ещё требуется [tracker bootstrap](../../../roadmap/delivery-workflow.md).

## Tracker

| Task | GitHub issue |
|---|---|
| `TASK-001` | [#18](https://github.com/K-Mickey/roots-of-rhythm/issues/18) |
| `TASK-002` | [#9](https://github.com/K-Mickey/roots-of-rhythm/issues/9) |
| `TASK-003` | [#19](https://github.com/K-Mickey/roots-of-rhythm/issues/19) |
| `TASK-004` | [#21](https://github.com/K-Mickey/roots-of-rhythm/issues/21) |
| `TASK-005` | [#20](https://github.com/K-Mickey/roots-of-rhythm/issues/20) |
| `TASK-006` | [#15](https://github.com/K-Mickey/roots-of-rhythm/issues/15) |
| `TASK-007` | [#16](https://github.com/K-Mickey/roots-of-rhythm/issues/16) |
| `TASK-008` | [#10](https://github.com/K-Mickey/roots-of-rhythm/issues/10) |
| `TASK-009` | [#17](https://github.com/K-Mickey/roots-of-rhythm/issues/17) |

## TASK-001: создать исполняемый каркас приложения

### Результат

Backend, frontend и PostgreSQL запускаются локально согласованными командами; quality и contract toolchain воспроизводимы из lockfiles.

### Scope

- создать в корне явные `backend/` и `frontend/` рядом с существующим `docs/`; внутри — минимальные source roots без пустых каталогов всех будущих contexts;
- сразу создать исполняемые entrypoints Litestar и Next.js и минимальные liveness/readiness health endpoints, нужные Compose;
- подключить Litestar, msgspec, Uvicorn, SQLAlchemy, Alembic и Psycopg 3 async;
- подключить Next.js, React, TypeScript и Mantine как основную design system;
- настроить PostgreSQL, backend и frontend как сервисы root Docker Compose; PostgreSQL использует named volume и healthcheck, application services ждут реальную готовность зависимостей;
- добавить environment example без секретов и отдельный migration entrypoint;
- заполнить backend `pyproject.toml` корректными project metadata и description, а Ruff, mypy, pytest и прочие только development tools поместить в uv `dev` dependency group;
- адаптировать базовые Ruff/mypy/pytest настройки из `local-setup/ncip-api`, но не копировать его project-specific exclusions, подавления типов и лишние dependencies;
- настроить uv/pnpm lockfiles, ESLint, Prettier, Vitest/RTL, Playwright и один OpenAPI linter;
- настроить generation/check TypeScript types из принятого OpenAPI;
- добавить root Makefile с `help`, setup/lock, Compose up/down/ps/logs, backend/frontend dev, migration/seed, format, lint, typecheck, unit/integration/E2E tests, contract check, build и aggregate `check`; цели остаются тонкими entrypoints без скрытой бизнес-логики;
- записать в `docs/development.md` только реально работающие команды.

### Проверка

- clean setup воспроизводится по документации;
- backend и frontend стартуют как на host, так и в Compose; healthchecks проходят, PostgreSQL доступен только локальному application окружению, а данные сохраняются после обычного `compose down`;
- lint, typecheck, contract check и production builds запускаются отдельными командами;
- generated API types соответствуют `docs/api/openapi.yaml`.

### Не входит

Domain entities, Genre endpoint/page, authentication, Caddy, Sentry/Grafana и production deployment.

## TASK-002: реализовать Genre aggregate и persistence Music Catalog

### Результат

Music Catalog хранит Genre как `ClassificationConcept(kind=genre)` с принятым минимальным lifecycle и опциональными metadata.

### Scope

- реализовать domain types Genre/ClassificationConcept, editorial status, historical period/geographic summary и publication rules как `msgspec.Struct` без зависимости от Litestar, HTTP DTO или persistence models;
- не использовать domain Struct как transport DTO: mapping между domain/application results и public DTO остаётся явным;
- публикация Genre требует только непустые `name + definition`; отсутствующие metadata не получают фиктивных defaults;
- создать SQLAlchemy mappings и Alembic migration в infrastructure Music Catalog;
- определить application-owned repository/UoW contracts и SQLAlchemy adapters;
- обеспечить стабильный opaque ID и archive вместо обычного физического удаления опубликованного объекта;
- не добавлять Style/Scene/Tradition pages, localization, graph DB или generic Entity model.

### Покрывает

`FR-001`–`FR-005`, `NFR-003`–`NFR-005`, `AC-1`, `AC-2`, часть `AC-9`.

### Проверка

- domain tests проверяют минимальную публикацию и отсутствие invented defaults;
- PostgreSQL integration tests проверяют mapping, migration, transaction ownership и public filtering Genre.

## TASK-003: реализовать GenreRelation Claim, Source и Evidence invariants

### Результат

Historical Knowledge хранит независимый GenreRelation Claim и публикует его только при выполнении полноты, Evidence и endpoint visibility rules.

### Scope

- реализовать Claim aggregate для GenreRelation со всеми пятью relation types, temporal/geographic context, explanation, provenance, editorial/evidence statuses и Evidence references;
- draft требует только различные существующие subject/target Genre IDs и relation type;
- publish требует полную содержательную форму и опубликованные endpoint Genre;
- `supported`, `disputed`, `unverified` соблюдают принятые Evidence invariants; `confidence` отсутствует;
- `overlaps_with` хранится один раз в каноническом порядке IDs;
- реализовать минимальные Source, SourceVersion и SourceFragment persistence границы, необходимые двум seed Evidence, без ingestion/RAG;
- public visibility relation повторно вычисляется при чтении из relation и обоих endpoint statuses.

### Покрывает

`FR-005`–`FR-009`, `FR-015`, `NFR-003`–`NFR-005`, `AC-3`–`AC-7`, `AC-9`, `AC-12`, `AC-13`.

### Проверка

- domain tests покрывают каждый relation/evidence status, conditional publication rules и canonical symmetric pair;
- integration tests покрывают независимую публикацию, скрытие при archive endpoint и повторное появление после его публикации;
- draft и reviewed/non-reviewed Evidence не раскрываются public query.

## TASK-004: добавить воспроизводимый controlled seed

### Результат

Чистая база воспроизводимо получает Swing, Jazz, Jump Blues и две опубликованные поддержанные relations из утверждённых источников.

### Scope

- добавить идемпотентный seed/import entrypoint;
- создать три опубликованных Genre без Performer, Group и Recording;
- создать `Swing developed_from Jazz` и `Swing contributed_to_emergence_of Jump Blues` с explanation, temporal/geographic context и provenance;
- создать Smithsonian Music и Library of Congress Sources/Fragments и прошедшие review supporting references;
- провести данные через те же domain publication invariants, не записывать published rows в обход модели;
- не создавать искусственные примеры остальных relation types.

### Покрывает

`FR-011`, `FR-012`, `AC-10`, `AC-11`.

### Проверка

- повторный запуск не создаёт дубликаты и не меняет стабильные identities;
- integration test на чистой БД подтверждает точный обязательный набор и отсутствие Performer/Group/Recording.

## TASK-005: реализовать public Genre overview query и endpoint

### Результат

`GET /api/v1/genres/{genre_id}` возвращает обязательную `GenreOverviewResponse` строго по OpenAPI 0.2.0 и не раскрывает непубличный Genre.

### Scope

- реализовать Discovery/application query для public Genre identity, definition, image, period, geography, history, formation и characteristic features;
- реализовать отдельный msgspec `GenreOverviewResponse` и тонкий Litestar handler;
- unknown, malformed, draft и archived ID возвращают одинаковые `404 GENRE_NOT_FOUND`;
- невозможность собрать overview даёт `500 INTERNAL_ERROR` с request ID;
- не загружать relations и Sources в этом query и не добавлять cache, ETag/revision token, auth или slug API.

### Покрывает

`FR-001`–`FR-005`, `FR-016`, `NFR-004`–`NFR-006`, `AC-1`, `AC-2`, Genre-часть `AC-9`, часть `AC-14`.

### Проверка

- contract/integration tests проверяют overview operation/example/schema, optional fields, `200/404/500` и отсутствие draft data;
- query-count regression check фиксирует bounded SQL count overview без произвольного latency threshold;
- architecture test подтверждает отсутствие Litestar/SQLAlchemy/transport DTO в domain modules; импорт msgspec в domain явно разрешён ADR-0004.

## TASK-006: реализовать public Genre relations query и endpoint

### Результат

`GET /api/v1/genres/{genre_id}/relations` возвращает ordered `GenreRelationsResponse` с публичными relations и reviewed Evidence references без N+1.

### Scope

- реализовать Discovery/application query только для видимых Genre relations;
- применить relation и endpoint Genre visibility, reviewed Evidence filtering, temporal/type/name sorting и вычисление `perspective`;
- вернуть relation ID, related Genre summary, type, perspective, explanation, contexts, evidence status и references в msgspec DTO;
- вернуть `[]` как успех при отсутствии relations, а `404/500` с общими stable codes по контракту;
- не возвращать Source bibliography и не добавлять pagination или per-relation endpoints.

### Покрывает

`FR-005`–`FR-010`, `FR-016`, `NFR-003`–`NFR-006`, `AC-3`–`AC-9`, часть `AC-14`, `AC-15`.

### Проверка

- contract/integration tests покрывают schema/example, `200/404/500`, empty success, все relation/evidence statuses и отсутствие draft/non-reviewed data;
- query-count regression check фиксирует bounded SQL count для двух seed relations и защищает от per-relation N+1.

## TASK-007: реализовать public Genre sources query и endpoint

### Результат

`GET /api/v1/genres/{genre_id}/sources` возвращает `GenreSourcesResponse` с дедуплицированной public bibliography без N+1.

### Scope

- реализовать Discovery/application query для Sources, на которые ссылается текущий public content Genre page;
- дедуплицировать Sources и сортировать по first public citation occurrence;
- не раскрывать SourceFragment text, review notes, rights-restricted locators и другие internal metadata;
- вернуть `[]` как успех при отсутствии public Sources, а `404/500` с общими stable codes;
- не добавлять per-source endpoint, pagination или общий snapshot/revision token.

### Покрывает

`FR-005`, `FR-007`, `FR-016`, `NFR-004`–`NFR-006`, `AC-4`, `AC-6`, часть `AC-14`, `AC-15`.

### Проверка

- contract/integration tests покрывают schema/example, `200/404/500`, empty success, deduplication/order и только public reviewed references;
- query-count regression check защищает bibliography от per-source N+1;
- на стабильном seed state каждый public relation `source_id` разрешается в sources projection.

## TASK-008: реализовать SSR Genre page на Next.js и Mantine

### Результат

Visitor открывает `/genres/{genre_id}` и получает адаптивную, доступную и содержательно понятную страницу по UI contract.

### Scope

- до кода страницы подготовить и отдельно утвердить лёгковесную UI/design specification: application shell, Mantine theme tokens, content width, typography, shared header/footer, page states и representative narrow/wide layouts; не начинать Genre-specific UI до этого checkpoint;
- сначала реализовать переиспользуемые shell/theme primitives, затем собрать Genre page на их основе;
- использовать generated OpenAPI types и три server-side requests без дополнительных per-item requests;
- построить Mantine-first application shell и три content groups без Tailwind и самописных базовых controls;
- реализовать required/optional sections, relation perspective labels, evidence labels/references и дедуплицированный Sources list;
- скрывать отсутствующие optional sections без пустых headings/cards/placeholders;
- не делать имя связанного Genre ссылкой;
- реализовать loading при client navigation, единый not-found, page error/retry для overview, inline error/retry для relations/sources и graceful broken-image state;
- сохранить semantic landmarks/headings/lists, keyboard/focus behavior, text alternatives и mobile-first reading order;
- initial HTML содержит основное содержание без обязательной пользовательской JavaScript-интерактивности.

### Покрывает

`FR-001`–`FR-010`, `FR-012`, `FR-016`, `NFR-002`, `NFR-006`, `AC-1`–`AC-9`, `AC-14`, `AC-15`.

### Проверка

- component tests покрывают populated/empty/not-found/page-error/section-error/broken-image и perspective/evidence presentations;
- accessibility checks подтверждают landmarks, heading order, names, focus и отсутствие color-only signals;
- Playwright smoke открывает seed Swing page с реальным backend/PostgreSQL и проверяет critical public scenario;
- visual review выполняется на Swing/Jazz/Jump Blues, узком и широком viewport; spacing калибруется без изменения UI contract.
- утверждённая design specification и общие shell/theme components проверяются отдельно от Genre-specific content.

## TASK-009: выполнить итоговую приёмку vertical slice

### Результат

Есть воспроизводимое evidence выполнения STORY-001 и перечень известных ограничений без скрытого переноса scope.

### Scope и проверка

- выполнить clean setup, migration и seed;
- запустить contract lint/drift check, backend/frontend lint, typecheck, tests и production builds;
- выполнить Playwright end-to-end scenario через реальные frontend, backend и PostgreSQL: поднять стек, открыть seed Swing page, проверить ключевое содержание и публичную relation/evidence presentation;
- пройти все 15 acceptance criteria и записать результат;
- проверить отсутствие локализации, Performer/Group/Recording, graph/search/vector DB, queues, authentication, Caddy и observability stack;
- актуализировать `docs/development.md`, API changelog и только те документы, фактическое поведение которых изменилось;
- подготовить tracker/PR evidence, но не создавать commit или PR без отдельной команды.

## Зависимости и критический путь

```text
TASK-001 scaffold → TASK-002 Genre
TASK-002 Genre → TASK-005 overview API
TASK-002 Genre → TASK-003 Claims/Evidence → TASK-004 seed
TASK-004 seed → TASK-006 relations API
TASK-004 seed → TASK-007 sources API

TASK-001 shell/toolchain ────────────────┐
TASK-005 overview API ─────────────────┤
TASK-006 relations API ───────────────┤─→ TASK-008 public UI → TASK-009 acceptance
TASK-007 sources API ────────────────┘
```

TASK-005 может развиваться после TASK-002 независимо от Claim. TASK-006 и TASK-007 зависят от TASK-003, а их seed-level verification — от TASK-004; после этого они могут выполняться параллельно. Frontend shell/theme часть TASK-008 может начаться после TASK-001, но integrated UI зависит от TASK-005–007. TASK-009 не является местом для накопления пропущенных tests: каждая предыдущая задача поставляет свои проверки.

## Подтверждения и checkpoints

- декомпозиция и создание новых перечисленных tests, fixtures и test configuration утверждены 2026-08-17; изменение уже существующих tests по-прежнему требует отдельного подтверждения;
- выполнить `/sync-tracker` dry run и подтвердить создание GitHub Project/items;
- до TASK-008 отдельно утвердить design specification; это не требует пересмотра уже принятого semantic UI contract;
- точные versions зависимостей фиксируются lockfiles при TASK-001 и не являются новым продуктовым решением;
- никаких production writes, branches, commits или PR без отдельных команд.

## История изменений

- 2026-08-17: Product Owner утвердил семь tasks и создание новых tests; TASK-001 уточнён до исполняемого Compose-каркаса с persistent PostgreSQL volume, healthchecks, dev dependencies/config и Makefile; TASK-006 получил design checkpoint и shared shell; TASK-007 — полный E2E.
- 2026-08-17: msgspec утверждён для отдельных domain и transport types; TASK-005/006 и проверки актуализированы под три API projections и локальные section errors.
- 2026-08-17: Product Owner разделил три public API operations на три work items; декомпозиция теперь содержит девять tasks, UI перенесён в TASK-008, acceptance — в TASK-009.

## Не создаём отдельные задачи

- «создать все таблицы» вне конкретных aggregates;
- общий repository/framework abstraction;
- Caddy, DDoS, Sentry/Grafana — это EPIC-012 и не блокирует локальный старт;
- authentication, Editorial UI, карта, RAG, MCP, media providers;
- Redis, queue, S3, Elasticsearch, vector или graph database.
