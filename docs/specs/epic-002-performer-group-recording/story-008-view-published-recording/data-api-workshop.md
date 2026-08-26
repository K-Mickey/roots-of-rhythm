# Data/API: опубликованная запись и исполнения песни

Статус: `accepted`

Story: [STORY-008](README.md).

OpenAPI обновляется отдельной задачей реализации после утверждения этого workshop.

## Public HTTP

`GET /api/v1/recordings/{recording_id}`

- без авторизации;
- `200` — `RecordingOverviewResponse`:
  - `id`, `title`, `recorded_period`, вычисляемая `first_release_date`, `description`, `isrc`;
  - `work_usages`: `{ work: { id, name }, usage_kind, position }`;
  - `credits`: published Person/Group summaries, role/instrument, `billing_role`, `credited_as`;
  - `genres`: published Genre summaries прямых Recording assignments;
  - `lyrics_usages`: упорядоченные фактически звучащие LyricsVersion и их published reading translations;
  - `origin_badges`: только published `supported` Claims `recording_origin`;
  - `listening_guide` nullable;
- unknown, malformed, draft, archived и deleted id — `404` `RECORDING_NOT_FOUND`;
- `500` `INTERNAL_ERROR` при сбое сборки.

Глобальный `GET /api/v1/recordings` не добавляется.

## Расширение Song overview

STORY-008 аддитивно расширяет `GET /api/v1/songs/{song_id}`:

```text
recording_genres[]
├── genre: { id, name }
└── recording_count

recordings[]
├── id
├── title
├── recorded_period
├── first_release_date
├── primary_credits[]
├── genre_ids[]
├── work_usage_kind
└── origin_badges[]
```

- `recordings` содержит distinct published Recording, связанные с Work любым usage kind;
- `first_release_date` вычисляется по published Release/Track после STORY-009 и до этого может быть `null`; отдельное дублирующее поле Recording не вводится;
- порядок: дата записи, дата первого выпуска, canonical title, id; неизвестные даты последними;
- `recording_genres` считает distinct Recording только по usages `complete` и `partial`;
- `medley_component` остаётся в хронологии, но не участвует в genre facets;
- facet и summary не копируются в Work aggregate и строятся Discovery query;
- все компактные summaries возвращаются без pagination в MVP; изменение требует измеренного endpoint cost и отдельного contract change.

## RecordingWorkUsage

- дочерняя entity Recording: `work_id`, `usage_kind`, optional `position`;
- публикация требует минимум один usage на published Work;
- `position` обязателен для двух и более `medley_component`, уникален внутри Recording;
- обычный `complete`/`partial` не требует position;
- один Work не дублируется внутри Recording с тем же usage kind.

## RecordingLyricsUsage

- дочерняя упорядоченная entity Recording;
- ссылается только на published `performable` LyricsVersion Work, присутствующего в RecordingWorkUsage;
- machine translation и `reading_translation` не могут быть usage;
- reading translations находятся обратным запросом `LyricsVersionRelation.translation_of`;
- отсутствие lyrics usages допустимо, включая инструментальную и неполностью описанную Recording.

## Origin Claims

`claim_kind=recording_origin`; subject — Recording, object — Work. Поддерживаемые predicates:

- `first_known_performance_of`;
- `first_recording_of`;
- `first_released_recording_of`;
- `recorded_by_work_author`.

Только `published + supported` Claim становится кратким origin badge. `unverified` и `disputed` остаются доступны редакционному workflow, но не превращаются в утверждающий публичный badge. Дата и позиция в списке не создают Claim автоматически.

`first_known_performance_of` допустим только если Recording фиксирует это исполнение. Для незаписанного события фиктивная Recording не создаётся.

## Query state страницы песни

Frontend принимает:

- `recording=<recording_id>` — выбранная Recording текущего Work;
- `genre=<genre_id>` — активный facet;
- `text=<lyrics_version_id>` — выбранный исполняемый текст или его reading translation.

Если параметр отсутствует или не принадлежит опубликованной проекции текущего Work, используется безопасное состояние по умолчанию: первый facet не выбран, Recording — первая в хронологии, text — первый usage выбранной Recording. При отсутствии lyrics usage показывается первая published Work LyricsVersion с явной пометкой «соответствие записи не подтверждено».
