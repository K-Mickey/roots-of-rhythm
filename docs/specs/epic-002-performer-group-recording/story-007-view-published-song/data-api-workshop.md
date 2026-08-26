# Data/API: опубликованная песня

Статус: `accepted`

Story: [STORY-007](README.md).

OpenAPI обновляется отдельной задачей реализации после утверждения этого workshop.

## Public HTTP

`GET /api/v1/songs`

- без авторизации, query и пагинации;
- `200` — `SongListResponse`: `{ items: [{ id, name }] }`;
- пустой корпус — `200` и `items: []`;
- только published, не soft-deleted MusicalWork;
- порядок по canonical title;
- `500` `INTERNAL_ERROR` при сбое чтения.

`GET /api/v1/songs/{song_id}`

- без авторизации;
- `200` — `SongOverviewResponse`:
  - `id`, `name`, `aliases`, `description`, `period`, `external_identities`;
  - `credits` — published WorkCredit с published Person: `{ person: { id, name }, role, credited_as }`;
  - `classifications` — published ClassificationConcept summaries по прямым assignments Work;
  - `related_works` — опубликованные направленные WorkRelation: `{ relation_type, work: { id, name } }`;
  - `lyrics_versions` — опубликованные metadata/body по политике прав;
- editorial status, deleted, timestamps, внутренний provenance и Evidence не входят в публичный overview;
- неизвестный, malformed, draft, archived и deleted id — `404` `SONG_NOT_FOUND`, сообщение «Материал не найден.»;
- `500` `INTERNAL_ERROR` при сбое сборки.

## LyricsVersion view

Публичная версия содержит:

```text
id
language_tag
label nullable
usage_kind: performable | reading_translation
creation_method: original | human_translation | machine_translation
body nullable
body_unavailable_reason nullable
credits[]
relations[]
```

- `language_tag` — канонизированный BCP 47 tag;
- `body` возвращается только при разрешающей rights/access policy Source;
- при недоступном теле metadata остаются публичными, а `body_unavailable_reason` содержит безопасную пользовательскую причину без внутренних rights notes;
- machine translation всегда `reading_translation` и явно маркируется;
- public response не возвращает draft LyricsVersion, credits или relations;
- порядок: `performable` перед `reading_translation`, затем `language_tag`, `label`, `id`.

## Публикационные правила

- MusicalWork требует canonical title и provenance; credits, classification, text и Recording опциональны.
- WorkCredit ссылается на Person и имеет роль; отсутствие известного автора не заменяется специальным Person.
- WorkRelation типов `translation_of`, `adaptation_of`, `arrangement_of`, `medley_of` требует published source/target Work, provenance и editorial status.
- LyricsVersion принадлежит одному Work. Исполняемый перевод и адаптация принадлежат производному Work; reading translation не создаёт Work автоматически.
- Source остаётся владельцем rights/access policy, SourceVersion — конкретной версии материала.

## Frontend

`/songs` на SSR читает list API. `/songs/{id}` читает overview; 404 приводит к route not-found. Выбор `?text=<lyrics_version_id>` допустим только внутри опубликованных версий текущего Work; невалидное значение заменяется первой доступной версией в порядке API.
