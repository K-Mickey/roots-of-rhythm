# Data/API: опубликованная группа

Статус: `accepted`

Story: [STORY-006](README.md).

## Public HTTP

`GET /api/v1/groups`

- без авторизации, query и пагинации;
- `200` — `GroupListResponse`: `{ items: [{ id, name }] }`;
- пустой корпус — `200` и `items: []`;
- только published, не soft-deleted Group;
- порядок по каноническому имени;
- `500` `INTERNAL_ERROR` при сбое чтения. Операция не использует `GROUP_NOT_FOUND`.

`GET /api/v1/groups/{group_id}`

- без авторизации;
- `200` — `GroupOverviewResponse`:
  - `id`, `name`;
  - `aliases` — массив строк, может быть пустым;
  - `description` — `null`, если нет;
  - `period` — `{ start, end }`; `start`/`end` — `null` или `TemporalBound` (тот же, что Genre/Person);
  - `primary_image` — nullable; в этом срезе всегда `null`;
  - `genres` — published Genre summaries по published ClassificationAssignment, порядок по имени жанра;
  - `members` — published GroupMembership с published Person, порядок по имени Person: `{ id, name, period, roles_or_instruments }`; `period` той же формы, что у Group; `roles_or_instruments` — массив строк, может быть пустым;
- editorial_status, deleted, timestamps, evidence, provenance не входят в ответ;
- неизвестный, malformed, draft, archived и deleted id — `404` `GROUP_NOT_FOUND`, сообщение «Материал не найден.»;
- `500` `INTERNAL_ERROR` при сбое сборки.

Контракт: [OpenAPI](../../../api/openapi.yaml) `0.6.0`. Additive к `0.5.0`.

## Group persistence (не HTTP)

Публикация Group требует только canonical name. Aliases, description и period хранятся и при публикации выдаются на get. Alias не дублирует canonical name без учёта регистра. Глобальная уникальность имени не действует.

## GroupMembership (не публичный write HTTP)

Обязательны PersonId и GroupId. Period, `roles_or_instruments`, evidence, provenance и editorial status — по [workshop 001/004](../../../domain/workshops/004-aggregate-boundaries.md). Публикация Group не требует ни одной membership. Публичный member виден только если membership и Person published.

`roles_or_instruments` — строки; справочник инструментов в этой story не создаётся.

## ClassificationAssignment Group→Genre

Тот же инвариант, что Person: explanation или claim_id, provenance, published Group и published Genre; до evidence references — только `unverified`.

## Frontend

`/groups` на SSR читает list API. Сбой не вызывает `notFound()`.

`/groups/{id}` на SSR читает overview. 404 → route not-found.
