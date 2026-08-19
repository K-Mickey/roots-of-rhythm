# Data/API: каталог опубликованных Genre

Статус: `accepted`

Story: [STORY-004](README.md).

## Public HTTP

`GET /api/v1/genres`

- без авторизации;
- без query-параметров и пагинации;
- `200` — `GenreListResponse`: `{ items: [{ id, name }] }`;
- пустой корпус — `200` и `items: []`;
- только published, не soft-deleted Genre;
- порядок `items` по каноническому имени;
- `500` `INTERNAL_ERROR` при сбое чтения (тот же безопасный ErrorResponse, что у overview).

Не публикуются draft, archived и deleted. Не возвращаются definition, period и relations.

Контракт: [OpenAPI](../../../api/openapi.yaml) `0.3.0`.

## Frontend

Страница `/genres` на SSR читает list API. Сбой не вызывает `notFound()` страницы Genre.
