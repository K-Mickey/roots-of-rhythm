# STORY-008: открыть опубликованную запись

Статус: `draft`

Tracker: [GitHub issue #34](https://github.com/K-Mickey/roots-of-rhythm/issues/34).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть конкретную запись песни: кто играл, когда, зачем она важна — и перейти к песне. Позже к этой записи подключится плеер.

## Проблема и измеримый результат

Запись ≠ песня ≠ релиз. Каталога записей нет: вход со страницы песни (и позже Genre/релиз). Story успешна, если published Recording открывается по `/recordings/{id}`, **обязательно** ссылается на песню, а страница песни показывает ссылки на все её published записи. «Послушать» на песне указывает на запись (ссылка; embed — EPIC-009).

## Контекст

Публикация Recording требует MusicalWork и >=1 primary RecordingCredit. ListeningGuide на этой странице; пустой скрыт. Не дублировать guide на песне.

## Functional requirements

- `FR-001` `/recordings/{id}` без авторизации. Нет `/recordings` каталога и нет пункта header «Записи».
- `FR-002` Recording нельзя опубликовать без MusicalWork. Страница записи содержит ссылку на `/songs/{id}`.
- `FR-003` Primary credits — ссылки на published Performer/Group.
- `FR-004` Поля обзора по [mvp-scope Recording](../../../product/mvp-scope.md): период, значение, жанры; пустые скрыты. Провайдеры не обязательны.
- `FR-005` ListeningGuide: если есть наблюдения — секция; иначе скрыта.
- `FR-006` Страница песни показывает все published Recording этой песни как ссылки; блок «послушать» использует запись (TBD: какая, если несколько).
- `FR-007` Появления на релизах скрыты или отсутствуют до STORY-009.
- `FR-008` Непубличный id — безопасный not-found.
- `FR-009` Seed: минимум одна published Recording с Work и primary credit.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` Нет list endpoint записей в этой story.
- `NFR-003` Плеер/MediaReference — EPIC-009.

## Acceptance criteria

1. Given seed Recording, when Visitor открывает `/recordings/{id}`, then `h1` записи и ссылка на песню.
2. Given страница этой песни, then имя/ссылка записи присутствует.
3. Given попытка published Recording без Work, then публикация невозможна (домен/application).
4. Given `/`, then нет каталога записей и нет header «Записи».
5. Given неизвестный id, then безопасный not-found.

## Данные и контракты

Recording, RecordingCredit, обязательный MusicalWorkId; обновление song page projection.

## In scope

Страница записи, инвариант Work, ссылки песня↔запись, seed, ListeningGuide empty/hide.

## Out of scope

Каталог записей; плеер; страница Track; compare covers.

## Ошибки и права

Как STORY-005. Отсутствие Work на published Recording — ошибка сборки, не публичный 200.

## Зависимости

STORY-007; STORY-005/006 для credits.

## Open questions

Какую запись предлагает «послушать» на песне, если их несколько — Product Owner (featured / первая по дате / только клик по списку).

## История изменений

- 2026-08-19: draft; Work обязателен; каталога нет.
