# Декомпозиция STORY-006

Статус: `accepted`.

Story: [STORY-006](README.md).  
Контракты: [UI](ui.md), [Data/API](data-api-workshop.md), [OpenAPI 0.6.0](../../../api/openapi.yaml).

Цель — минимальные work items каталога и страницы группы.

## Tracker

| ID | Issue |
|---|---|
| `TASK-001` | [#37](https://github.com/K-Mickey/roots-of-rhythm/issues/37) |
| `TASK-002` | [#38](https://github.com/K-Mickey/roots-of-rhythm/issues/38) |
| `TASK-003` | [#39](https://github.com/K-Mickey/roots-of-rhythm/issues/39) |
| `TASK-004` | [#40](https://github.com/K-Mickey/roots-of-rhythm/issues/40) |

## TASK-001: Group и GroupMembership persistence

### Результат

Music Catalog хранит Group (имя, aliases, description, период существования, editorial lifecycle) и отдельный aggregate GroupMembership (PersonId, GroupId, period, roles_or_instruments, provenance, editorial status). Публикация Group требует только каноническое имя и не требует состава.

### Scope

- domain `Group` / `GroupMembership` как `msgspec.Struct` без HTTP/ORM;
- period: `TemporalBound` start/end, граница nullable;
- `roles_or_instruments` — tuple строк, не catalog;
- SQLAlchemy mapping, Alembic, repository/UoW, soft-delete, `FOR UPDATE` на write (ADR-0006);
- одинаковые canonical name допустимы.

### Покрывает

`FR-001`, `FR-002`, `FR-006` (хранение), `FR-008`, `NFR-003`, AC-5/6.

### Проверка

Domain и PostgreSQL: publish Group без membership; list_published скрывает draft/archived/deleted; membership с/без period и roles.

### Не входит

HTTP, seed, ClassificationAssignment, instrument dictionary, Evidence UI.

## TASK-002: assignment Group→Genre и seed

### Результат

Публикация ClassificationAssignment на Group работает. Seed содержит четыре published Group, membership и жанровые назначения.

### Scope

- `create_for_group` и publish: published Group + published Genre, explanation-or-claim, provenance, только `unverified`;
- seed, идемпотентный: Charlie Parker Quintet (Jazz, Charlie Parker); Count Basie Orchestra (Swing, Count Basie); Benny Goodman Orchestra (Swing, Benny Goodman); Tympany Five (Jump Blues, Louis Jordan);
- хотя бы у части membership — period и `roles_or_instruments`.

### Покрывает

`FR-005`, `FR-006`, `FR-008`, AC-1/3/6.

### Проверка

Повторный seed не дублирует identity; publish assignment отклоняется на unpublished Group/Genre; Group без membership публикуется.

### Не входит

Related на странице Genre (STORY-010); публичный HTTP.

## TASK-003: публичный list и overview API

### Результат

`GET /api/v1/groups` и `GET /api/v1/groups/{group_id}` соответствуют OpenAPI 0.6.0.

### Scope

Discovery queries, Litestar, `GROUP_NOT_FOUND` / `INTERNAL_ERROR`. List — `id` + `name`. Get — публичные поля Group, `members`, `genres`; без editorial/deleted/timestamps/evidence/provenance.

### Покрывает

`FR-001`, `FR-002`, `FR-005`, `FR-006`, `NFR-002`, AC-1/5/7 (API).

### Проверка

Contract-check; HTTP 200 list/get; 404 непубличного id; пустой list 200; members только published Person.

### Не входит

Frontend.

## TASK-004: страницы `/groups`, `/groups/{id}` и header

### Результат

Visitor из header открывает каталог и страницу группы на SSR.

### Scope

Routes, header «Группы», скрытие пустых секций, membership ссылки + period/roles если есть, page error vs not-found, главная без `/groups/{id}`. Нет Recording.

### Покрывает

`FR-003`–`FR-007`, `NFR-001`, AC-1–5, AC-7.

### Проверка

SSR HTML содержит `href` имён групп и Performer; header; `/` без group detail-ссылок; сбой list — PageError.

### Не входит

Editorial UI, плеер, related на Genre.

## Зависимости

```text
TASK-001 Group+Membership → TASK-002 assignment/seed → TASK-003 API → TASK-004 UI
```

## Не создаём отдельные задачи

- Elasticsearch, очередь, граф;
- instrument catalog;
- Recording/Work/Release.
