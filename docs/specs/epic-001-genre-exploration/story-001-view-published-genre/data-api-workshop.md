# Data/API Workshop: публичная Genre page

Статус: `accepted`

Story: [STORY-001](README.md).  
UI: [accepted UI contract](ui.md).

Цель: согласовать публичный read model и HTTP-поведение STORY-001 до создания OpenAPI contract. Документ не утверждает схему хранения, ORM или frontend framework.

## Уже утверждённые ограничения

- endpoint публичный и доступен Visitor без авторизации;
- в ответ не попадают draft, archived и другие непубличные Genre/Claim/Evidence;
- неизвестный и непубличный Genre неразличимы для Visitor;
- read model является проекцией и не становится источником истины для Genre, Claim, Source или MediaAsset;
- первая операция только читает один Genre: pagination, idempotency key и concurrent-write semantics ей не нужны;
- response не раскрывает internal editorial statuses, review notes, audit metadata, storage keys и SourceFragment text;
- локализация и localized/SEO URLs отложены и не должны незаметно попасть в STORY-001.

## DQ-API-01. Как идентифицировать Genre

### Варианты

1. `GET /api/v1/genres/{genre_id}` с неизменяемым opaque ID.
2. Endpoint по slug, например `/genres/swing`.
3. Один path parameter принимает и ID, и slug.

### Рекомендация

Для API использовать только opaque `genre_id`. Он не зависит от названия и языка. Человекочитаемый web route и redirect при смене slug лучше решить в story навигации/SEO. Гибрид ID/slug создаёт неоднозначный namespace без пользы для первой story.

Решение Product Owner 2026-08-16: STORY-001 использует ID. Slug визуально предпочтительнее, но не входит в первый contract. Его добавление как web-route concern оценивается в story навигации/SEO, без гибридного ID/slug parameter.

## DQ-API-02. Один атомарный response или несколько projections

### Варианты

1. Один response с Genre, relations, evidence references и sources.
2. Отдельные requests для overview, relations и sources.

### Принятое решение

Первоначально 2026-08-16 был принят один атомарный `GenrePageResponse`. Product Owner заменил это решение 2026-08-17 на три секционные projections:

1. `GET /api/v1/genres/{genre_id}` — `GenreOverviewResponse`: identity, definition, image, period, origin/history/formation и characteristic features.
2. `GET /api/v1/genres/{genre_id}/relations` — `GenreRelationsResponse`: все видимые relation cards одним bounded list, включая evidence references, без запроса на каждый Claim.
3. `GET /api/v1/genres/{genre_id}/sources` — `GenreSourcesResponse`: дедуплицированная библиография всех public Evidence references текущей Genre page, без endpoint на каждый Source.

Границы не повторяют таблицы или aggregates: они отражают независимые UI-секции и loading/error lifecycle. Overview обязателен для страницы; relations и sources могут независимо завершиться пустым успехом или явной inline error. Pagination, per-relation и per-source endpoints в STORY-001 не вводятся.

`source_id` в relation reference может быть сопоставлен с bibliography. Каждая projection самосогласована на момент своего read; общий snapshot/revision token не вводится без сценария, поэтому кратковременное расхождение при concurrent editorial publication допустимо.

## DQ-API-03. Как передавать отсутствующие данные

### Варианты

1. Опускать все optional keys.
2. Всегда возвращать скалярные optional fields как `null`, а коллекции как `[]`.
3. Смешать оба подхода для разных секций.

### Рекомендация

Выбрать вариант 2: стабильная форма response упрощает typed frontend. `null` означает «значение не опубликовано», `[]` — «опубликованных элементов нет». Frontend скрывает оба варианта. Future sections не добавляются в response до появления их story.

## DQ-API-04. Как выразить приблизительное время

### Варианты

1. Только строка: `конец 1920-х — 1940-е`.
2. Только точные `start_year`/`end_year`.
3. Человекочитаемый label и optional structured bounds с precision.

### Рекомендация

Общий `HistoricalPeriodView` для Genre period и relation temporal context:

```text
HistoricalPeriodView
├── label
├── start optional: year + precision
└── end optional: year + precision
```

Начальный precision enum:

```text
exact_year | circa_year | decade | early_decade | mid_decade | late_decade
```

Пример: `label="конец 1920-х — 1940-е"`, start `{year: 1920, precision: late_decade}`, end `{year: 1940, precision: decade}`. `year` здесь опора для decade, а не утверждение о 1920 годе. Open bounds допустимы. Frontend показывает `label`, а не восстанавливает историческую формулировку из чисел. Relations приходят в уже отсортированном порядке.

## DQ-API-05. Как выразить географию

### Варианты

1. Свободный текст.
2. Ссылки только на структурированные Place.
3. Текстовый summary и optional `places[]` после появления Place catalog.

### Рекомендация

Заложить `GeographicContextView { summary }`. Сложный контекст вроде «США, прежде всего городские сцены Среднего Запада» не сводится к одной точке. `places[]` можно добавить non-breaking после появления утверждённой Place identity. Не вводить Place и координаты только ради первой Genre page.

## DQ-API-06. В каком формате передавать текст

### Варианты

1. Plain text с абзацами через newline.
2. Markdown.
3. Готовый HTML.
4. Structured rich-text tree.

### Рекомендация

Для STORY-001 использовать plain Unicode text. Абзацы разделяются `\n\n`; HTML не принимается и не интерпретируется. Этого достаточно для definition, historical context, formation и explanation. Rich text нужно вводить вместе с реальным сценарием ссылок, inline citations или сложного редактирования.

## DQ-API-07. Как передать image

### Рекомендация

`primary_image` является public projection MediaAsset, а не URL в Genre:

```text
PublicImageView
├── id
├── url
├── alt_text
├── width optional
├── height optional
├── attribution_text optional
└── attribution_url optional
```

API не возвращает storage key и не обещает конкретный S3/CDN provider. MediaAsset попадает в public response только если editorial и rights/access policies это разрешают.

## DQ-API-08. Как связать relations, Evidence и Sources

### Рекомендация

- `relations[]` содержит public relation ID, related Genre summary, type, perspective, explanation, temporal/geographic contexts, evidence status и `evidence_references[]`;
- `evidence_references[]` содержит `source_id`, role и public locator; SourceFragment ID и полный fragment text не раскрываются;
- `sources[]` — дедуплицированный bibliographic list всех Source, на которые ссылается public content;
- цитационный номер вычисляется из порядка `sources[]`, а не хранится как отдельная истина;
- в стабильном public state каждый `source_id` из relations projection присутствует в отдельной sources projection; общая database snapshot между requests не обещана;
- citation marker вычисляется только если `source_id` разрешается в успешно загруженной bibliography; при временном расхождении UI не выдумывает Source metadata и сохраняет public locator из Evidence reference;
- `perspective` — public read-model field `subject | target | symmetric`, а не domain enum или отдельная Claim.

Открытый вопрос: должен ли Source locator быть структурой (`url`, page, chapter, timestamp) или одной строкой. Рекомендация: на старте `locator_text` и optional safe `external_url`; отдельные page/timestamp fields добавлять по сценарию.

## DQ-API-09. HTTP-ошибки и версионирование

### Рекомендация

- `200` — полная запрошенная overview, relations или sources projection;
- `404` + `GENRE_NOT_FOUND` — malformed, unknown, draft и archived ID, без уточнения причины;
- `500` + `INTERNAL_ERROR` — response нельзя безопасно собрать;
- error body содержит stable `code`, safe `message`, optional `details` и `request_id`;
- transport version фиксируется в path `/api/v1`; additive optional fields и enum values всё равно требуют обновления contract/changelog и явной обработки неизвестных enum на frontend;
- cache headers, ETag и conditional GET не фиксируются без performance requirement.

## DQ-API-10. Как объяснить `disputed`

При формализации response выявились два разных смысла:

- `explanation` объясняет, в чём состоит сама Genre relation;
- отдельный текст должен объяснить, в чём состоит существенное разногласие в Evidence или интерпретации.

Варианты:

1. Перегрузить `explanation` обоими смыслами.
2. Добавить `dispute_summary`: `null` для `unverified`/`supported` и обязательная непустая строка для `disputed`.
3. Заменить узкое поле на общее `evidence_note`, допустимое при любом evidence status.

Решение Product Owner 2026-08-16: оставить одно `explanation`. Для `disputed` оно объясняет и саму relation, и существенное расхождение источников или интерпретаций. Фраза «источники расходятся» без описания сути не считается заполнением. Evidence roles `supports` и `opposes` показывают стороны разногласия. `dispute_summary` и `evidence_note` не вводятся.

## Примерные формы responses

Это не JSON Schema, а проверка границ и связей:

```text
GenreOverviewResponse
├── id
├── name
├── definition
├── primary_image nullable
├── period nullable
├── geography_or_origin nullable
├── historical_context nullable
├── formation nullable
└── characteristic_features[]

GenreRelationsResponse
├── genre_id
└── relations[]
│   ├── id
│   ├── related_genre: id + name
│   ├── relation_type
│   ├── perspective
│   ├── explanation
│   ├── temporal_context
│   ├── geographic_context
│   ├── evidence_status
│   └── evidence_references[]

GenreSourcesResponse
├── genre_id
└── sources[]
```

## Принятые решения

Product Owner подтвердил DQ-API-01–10 2026-08-16. В DQ-API-01 slug сохранён как визуально предпочтительный кандидат для будущего web route. DQ-API-10 не добавляет отдельное поле для разногласия. DQ-API-02 заменён решением Product Owner 2026-08-17: overview, relations и sources стали тремя отдельными projections.
