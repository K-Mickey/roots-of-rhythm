# Data/API: опубликованный исполнитель

Статус: `accepted`

Story: [STORY-005](README.md).

## Public HTTP

`GET /api/v1/performers`

- без авторизации, query и пагинации;
- `200` — `PerformerListResponse`: `{ items: [{ id, name }] }`;
- пустой корпус — `200` и `items: []`;
- только published, не soft-deleted Person;
- порядок по каноническому имени;
- `500` `INTERNAL_ERROR` при сбое чтения. Операция не использует `PERFORMER_NOT_FOUND`.

`GET /api/v1/performers/{performer_id}`

- без авторизации;
- `200` — `PerformerOverviewResponse` с каждым публичным content-полем Person плюс изображение и жанры:
  - `id`, `name` (каноническое имя);
  - `aliases` — массив строк, может быть пустым;
  - `biography` — `null`, если нет;
  - `birth_date` / `death_date` — `null` или `{ year: int, precision }`, где `precision` — `exact_year | circa_year | decade | early_decade | mid_decade | late_decade` (тот же `TemporalBound`, что у Genre);
  - `external_identities` — массив `{ provider, identifier, url }`; `url` nullable; может быть пустым;
  - `primary_image` — nullable; в этом срезе всегда `null`;
  - `genres` — published Genre summaries по published ClassificationAssignment при опубликованных Person и Genre, порядок по имени жанра;
- внутренние `editorial_status`, deleted и timestamps не входят в ответ;
- неизвестный, malformed, draft, archived и deleted id — `404` `PERFORMER_NOT_FOUND`, сообщение «Материал не найден.»;
- `500` `INTERNAL_ERROR` при сбое сборки.

Контракт: [OpenAPI](../../../api/openapi.yaml) `0.5.0`. Additive к `0.4.0`: новые ключи overview; list без изменений.

## Person persistence (не HTTP)

Публикация Person требует только canonical name. Aliases, biography, даты и identities хранятся и при публикации выдаются на get, даже если пусты/`null`. Alias не дублирует canonical name без учёта регистра. Пара `provider` + `identifier` уникальна внутри Person. Глобальная уникальность canonical name не действует.

## ClassificationAssignment (не публичный HTTP в этой story)

Aggregate хранит `explanation` или `claim_id` (достаточно одного), обязательный provenance, `evidence_status` и editorial status.

Публикация assignment требует:

- explanation или claim_id;
- provenance;
- published Person и published Genre (read-only проверка, без cascade);
- до модели evidence references — только `evidence_status=unverified`; `supported` и `disputed` можно держать в draft, но не публиковать.

Публичная связь на overview видна только если assignment, Person и Genre published.

## Frontend

`/performers` на SSR читает list API. Сбой не вызывает `notFound()`.

`/performers/{id}` на SSR читает overview. 404 → route not-found.
