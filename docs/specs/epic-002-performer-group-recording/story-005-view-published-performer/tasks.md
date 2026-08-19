# Декомпозиция STORY-005

Статус: `accepted`.

Story: [STORY-005](README.md).  
Контракты: [UI](ui.md), [Data/API](data-api-workshop.md), [OpenAPI 0.5.0](../../../api/openapi.yaml).

Цель — минимальные work items каталога и страницы исполнителя. Tracker TASK issues создаются только после dry run и подтверждения Product Owner.

## TASK-001: Person aggregate и persistence People Catalog

### Результат

People Catalog хранит Person с каноническим именем, aliases, biography, birth/death с точностью, external identities и editorial lifecycle. Публикация требует только каноническое имя.

### Scope

- domain `Person` как `msgspec.Struct` без HTTP/ORM;
- value objects: aliases без case-insensitive дубля canonical name; `PersonDate { year, precision }`; `ExternalIdentity { provider, identifier, url? }` с уникальностью пары provider+identifier внутри Person;
- SQLAlchemy mapping, Alembic migration, repository/UoW, soft-delete, replace-content path;
- стабильный opaque ID; одинаковые canonical name допустимы (нет глобального unique index имени).

### Покрывает

`FR-001`, `FR-002`, `FR-007`, `FR-008` (хранение), часть `NFR-002`.

### Проверка

Domain и PostgreSQL integration для publish, list_published, скрытие draft/archived/deleted; optional content fields; отсутствие unique-constraint на canonical name.

### Не входит

Group, Recording, MediaAsset, публичный HTTP.

## TASK-002: ClassificationAssignment и seed

### Результат

Music Catalog хранит ClassificationAssignment Person→Genre с explanation или claim_id, provenance и evidence_status. Seed содержит шесть published исполнителей и указанные жанровые назначения.

### Scope

- assignment aggregate: target person + concept genre, editorial status, explanation или claim_id, provenance, evidence_status;
- публикация: explanation-or-claim, provenance, published Person и published Genre; до evidence references — только `unverified`;
- seed через domain services, идемпотентный; короткие explanation и provenance на seed assignments;
- Genre corpus без изменений смысла.

### Покрывает

`FR-006`, `FR-008`.

### Проверка

Seed повторно не дублирует identity; assignments читаются для published Person; publish отклоняется без explanation/claim, provenance или unpublished endpoints.

### Не входит

Обратный список на странице Genre (STORY-010); provenance/evidence UI; evidence references для `supported`/`disputed`.

## TASK-003: публичный list и overview API

### Результат

`GET /api/v1/performers` и `GET /api/v1/performers/{performer_id}` соответствуют OpenAPI 0.5.0.

### Scope

Discovery queries, Litestar router, `PERFORMER_NOT_FOUND` / `INTERNAL_ERROR`. List — `id` + `name`. Get — все публичные Person content-поля, `primary_image`, `genres`; без editorial_status/deleted/timestamps.

### Покрывает

`FR-001`, `FR-002`, `FR-006`, `FR-007`, `NFR-002`, AC-1/5/6/7 (API).

### Проверка

Contract-check; HTTP 200 list/get; 404 непубличного id; пустой list 200; keys overview всегда присутствуют.

### Не входит

Frontend, поиск, пагинация.

## TASK-004: страницы `/performers`, `/performers/{id}` и header

### Результат

Visitor из header открывает каталог и страницу исполнителя на SSR.

### Scope

Routes, header «Исполнители», скрытие пустых секций (aliases, био, даты, identities, жанры, image), page error vs not-found, главная без `/performers/{id}`. URL identity — ссылка; без URL — текст.

### Покрывает

`FR-003`–`FR-007`, `NFR-001`, `NFR-003`, AC-1–7.

### Проверка

SSR HTML содержит `href` имён; header; `/` без detail-ссылок исполнителей; сбой list — PageError; заполненные optional-поля видны.

### Не входит

Editorial UI, плеер, связанные сущности на Genre.

## Зависимости

```text
TASK-001 Person → TASK-002 assignment/seed → TASK-003 API → TASK-004 UI
```

## Не создаём отдельные задачи

- Elasticsearch, очередь, граф;
- Group/Recording/Work/Release;
- MediaAsset upload;
- GitHub TASK issues до подтверждения dry run.
