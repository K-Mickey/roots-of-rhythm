# Декомпозиция STORY-008

Статус: `accepted`.

Story: [STORY-008](README.md).  
Контракты: [UI](ui.md), [Data/API](data-api-workshop.md), [ADR-0007](../../../decisions/0007-musical-work-recording-and-origin-boundaries.md).

Цель — реализовать Recording, публичный каталог и объединённое изучение исполнений одного Work без дерева covers. Tracker TASK issues создаются только после dry run и отдельного подтверждения Product Owner.

## TASK-001: Recording, credits и Work usages

Tracker: [#49](https://github.com/K-Mickey/roots-of-rhythm/issues/49).

### Результат

Music Catalog хранит Recording с metadata, ISRC, credits и одним или несколькими Work usages. Публикация требует published Work usage и primary credit.

### Scope

- Recording aggregate и persistence lifecycle;
- RecordingCredit для Person/Group без ограничения количества;
- owned `RecordingWorkUsage { work_id, usage_kind, position }`;
- `complete | partial | medley_component`, ordering/uniqueness rules;
- optional recorded period, description и ISRC; first release date остаётся вычисляемой Release/Track projection;
- migrations, repository/UoW, soft-delete и write locks.

### Покрывает

`FR-001`–`FR-004`, `FR-008`–`FR-010`, `NFR-002`, AC-1/4/5/11.

### Проверка

Publish validation, several credits, single Work, partial and ordered medley, repeated audio identity not tied to Track, hidden draft/archived/deleted.

### Не входит

Release/Track migration, Session/Take/Master, Recording relations и HTTP.

## TASK-002: RecordingLyricsUsage и переводы

Tracker: [#50](https://github.com/K-Mickey/roots-of-rhythm/issues/50).

### Результат

Recording ссылается на фактически звучащие texts, а reading translations находятся без копирования ссылок в каждую Recording.

### Scope

- owned ordered RecordingLyricsUsage;
- LyricsVersion должна быть `performable`, published и принадлежать Work usage Recording;
- запрет machine/reading translation usage;
- Discovery query published `translation_of` versions;
- отсутствие usage допустимо.

### Покрывает

`FR-011`, `FR-015`, `NFR-001`, AC-9.

### Проверка

Одна и несколько языковых частей, invalid foreign Work, machine rejection, instrumental Recording, hidden draft translations, fallback Work text metadata.

### Не входит

Автоматическая транскрипция и временные коды строк текста.

## TASK-003: Recording API и отдельная страница

Tracker: [#51](https://github.com/K-Mickey/roots-of-rhythm/issues/51).

### Результат

OpenAPI и приложение предоставляют глобальный каталог и `GET /api/v1/recordings/{id}` / SSR detail с Work links, credits, жанрами, текстами и ListeningGuide.

### Scope

- `RecordingOverviewResponse`, `RECORDING_NOT_FOUND`, `INTERNAL_ERROR`;
- published related entities only;
- rights-aware lyrics translations;
- page sections и safe empty states;
- `GET /api/v1/recordings`, SSR `/recordings` и header item с title, primary credits, периодом и Genre;
- API changelog/contract check;

### Покрывает

`FR-001`–`FR-005`, `FR-007`–`FR-011`, `NFR-001`–`NFR-003`, AC-1/4/5/10/11.

### Проверка

List/detail HTTP 200/404, SSR content and links, no draft leakage, empty catalog/guide/lyrics.

### Не входит

Song page projection, player и Release appearances до STORY-009.

## TASK-004: жанровые фасеты и хронология Work

Tracker: [#52](https://github.com/K-Mickey/roots-of-rhythm/issues/52).

### Результат

Song overview аддитивно возвращает компактную хронологию Recording и независимые genre facets с distinct counts.

### Scope

- Discovery query по RecordingWorkUsage и published Recording assignments;
- facet counts для `complete`/`partial`, исключение `medley_component`;
- порядок date recorded → first release → title → id, unknown last;
- summaries с primary credits, genre IDs и usage kind;
- grouping metadata остаётся read projection;
- без pagination в текущем bounded corpus.

### Покрывает

`FR-006`, `FR-012`, `FR-013`, `FR-016`, `NFR-002`, AC-2/3/5/6.

### Проверка

Distinct counts, duplicate assignments, medley exclusion, unknown dates, several performers/genres, deterministic ties, zero/one/many Recording.

### Не входит

Запись фасетов в Work, search index и постоянная Interpretation.

## TASK-005: origin Claims и публичные бейджи

Tracker: [#53](https://github.com/K-Mickey/roots-of-rhythm/issues/53).

### Результат

Historical Knowledge описывает разные виды первенства Recording без `is_original`; публичный overview показывает только supported badges.

### Scope

- `claim_kind=recording_origin` и четыре predicates из Data/API workshop;
- subject Recording, object Work, provenance/evidence/editorial rules обычного Claim;
- projection только `published + supported`;
- никакого Claim из даты или порядка автоматически;
- точные пользовательские labels, без общего «Оригинал».

### Покрывает

`FR-013`, `FR-014`, AC-7/8.

### Проверка

Первая performance/recording/release у разных Recording; unverified/disputed не становятся badges; ранняя дата без Claim не получает роль.

### Не входит

RecordingRelation remix/edit, автоматический cover detection и ranking значимости.

## TASK-006: объединённая Song page

Tracker: [#54](https://github.com/K-Mickey/roots-of-rhythm/issues/54).

### Результат

Visitor переключает Recording, genre facet и text на `/songs/{id}` без полной перезагрузки; URL сохраняет контекст.

### Scope

- zero/one/many layouts;
- central Recording content, right chronology, mobile horizontal placement;
- visual grouping by primary Person/Group;
- accessible `recording`, `genre`, `text` controls;
- query validation, back/forward, SSR initial state;
- fallback Work text с явной пометкой;
- ListeningGuide выбранной Recording в центральном блоке;
- другие Work usages выбранной Recording без дублирования открытого Work;
- общий компактный lyrics switcher на Song и Recording detail с query history и безопасной нормализацией;
- links from Recording and готовность links from Performer/Genre projections.

### Покрывает

`FR-006`, `FR-011`–`FR-016`, `NFR-001`, `NFR-004`, `NFR-005`, AC-2/3/6–10.

### Проверка

Keyboard navigation, no full reload, direct query URLs, invalid IDs, mobile layout, genre filtering, text switching, ListeningGuide выбранной Recording and SSR content.

### Не входит

Player, pagination и persisted user preferences.

## TASK-007: seed и приёмка STORY-008

Tracker: [#55](https://github.com/K-Mickey/roots-of-rhythm/issues/55).

### Результат

Controlled corpus доказывает одну и несколько Recording, разные жанры, неизвестные даты, origin Claims и text usages; acceptance document фиксирует результаты всех checks.

### Scope

- несколько Recording Sixteen Tons для Merle Travis, Tennessee Ernie Ford и Stevie Wonder только с проверенными metadata/provenance;
- published Person для этих credits добавляются или переиспользуются через People Catalog; недостающие Genre concepts создаются только по classification policy и проверенному источнику;
- Recording существующих seeded Works/People там, где данные подтверждены;
- минимум один supported origin Claim, один unknown-date case, разные Genre и один lyrics usage/translation metadata case;
- идемпотентный seed;
- domain/API/frontend/browser checks и diff review.

### Покрывает

`FR-009` и все AC/NFR STORY-008.

### Проверка

Команды из `docs/development.md`; повторный seed; contract lint; required suites; фактические ограничения источников и непроверенные checks перечислены в acceptance.

### Не входит

Полный каталог всех известных covers Sixteen Tons и copyrighted lyrics body без прав.

## Зависимости

```text
TASK-001 Recording/WorkUsage ─┬─> TASK-002 LyricsUsage ─┐
                              ├─> TASK-003 Recording API/page
                              └─> TASK-004 facets/chronology ─┬─> TASK-006 Song page
TASK-005 origin Claims ───────────────────────────────────────┘
TASK-002/003/004/005/006 ───────────────────────────────────────> TASK-007 seed/acceptance
```

## Breaking changes и подтверждения

- Замена будущего одиночного MusicalWorkId на usages выполняется до появления production Recording data; если поле уже существует к старту задачи, migration создаёт один `complete` usage на строку.
- OpenAPI расширяется аддитивно; версия и changelog фиксируются в TASK-003/004.
- Тесты изменяются только после отдельного явного подтверждения согласно правилам проекта.
- GitHub issues, branch, commit и PR не создаются без отдельных команд.

## Не создаём отдельные задачи

- Interpretation, Session/Take/Master и дерево covers;
- RecordingRelation remix/edit без подтверждённого сценария;
- Elasticsearch, graph DB, очередь или pagination без измеренной необходимости;
- собственный player.
