# STORY-008: открыть опубликованную запись

Статус: `accepted`

Tracker: [GitHub issue #34](https://github.com/K-Mickey/roots-of-rhythm/issues/34).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть конкретную запись песни, понять кто, когда и в каком жанре её исполнил, а на странице песни переключаться между известными записями и текстами без потери общего контекста произведения.

## Проблема и измеримый результат

Запись ≠ песня ≠ релиз. Каталога записей нет: вход со страницы песни, Performer/Group и позже Genre/Release. Story успешна, если published Recording открывается по `/recordings/{id}`, имеет минимум один Work usage, а `/songs/{id}` показывает хронологию, жанровые фасеты и выбранную Recording. Историческое первенство подтверждается Claims, а не положением в списке.

## Контекст

Публикация Recording требует >=1 `RecordingWorkUsage` на published Work и >=1 primary RecordingCredit. Recording может использовать несколько Works и несколько фактически звучащих LyricsVersion. Published ListeningGuide показывается на странице записи и в центральном блоке выбранной Recording на странице песни.

## Functional requirements

- `FR-001` `/recordings` и `/recordings/{id}` доступны без авторизации; header содержит пункт «Записи».
- `FR-002` Recording нельзя опубликовать без хотя бы одного published Work usage. Страница записи содержит ссылки на все её published Works.
- `FR-003` Primary credits — ссылки на published Performer/Group.
- `FR-004` Поля обзора по [mvp-scope Recording](../../../product/mvp-scope.md): период, значение, жанры; пустые скрыты. Провайдеры не обязательны.
- `FR-005` Published ListeningGuide показывается на `/recordings/{id}` и в центральном блоке выбранной Recording на `/songs/{id}`; если наблюдений нет, секция скрыта.
- `FR-006` Страница песни показывает published Recording: при одной — содержимое в центре без боковой колонки, при нескольких — выбранную Recording в центре и список справа; переключение выполняется без полной перезагрузки через `?recording=<id>`.
- `FR-007` Появления на релизах скрыты или отсутствуют до STORY-009.
- `FR-008` Непубличный id — безопасный not-found.
- `FR-009` Seed: минимум одна published Recording с Work и primary credit.
- `FR-010` RecordingWorkUsage имеет `complete | partial | medley_component` и optional position; обычная Recording имеет один `complete`, medley допускает несколько упорядоченных usages.
- `FR-011` RecordingLyricsUsage хранит упорядоченные ссылки только на фактически звучащие `performable` LyricsVersion Works этой Recording. Переводы для чтения подтягиваются через LyricsVersionRelation и выбираются через `?text=<id>`.
- `FR-012` Страница Work раздельно показывает независимую классификацию произведения и фасеты `{ genre, recording_count }` по distinct published Recording. Фасеты учитывают `complete`/`partial`, исключают `medley_component` и фильтруют список через `?genre=<id>`.
- `FR-013` Recording сортируются по дате записи, затем по дате первого выпуска; неизвестные даты идут последними. Список называется хронологией известных записей и не назначает original.
- `FR-014` Claims `recording_origin` показывают отдельные бейджи `first_known_performance_of`, `first_recording_of`, `first_released_recording_of`, `recorded_by_work_author` только при `published + supported`. `is_original` и обязательный parent Recording не вводятся.
- `FR-015` Невалидный, чужой или непубличный `recording`, `genre` или `text` не раскрывает данные и заменяется безопасным состоянием по умолчанию.
- `FR-016` Из Performer/Group или Genre ссылка может открыть тот же `/songs/{id}` с релевантным `recording`; группировка по primary credit существует только в Discovery read model.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` Глобальный list endpoint возвращает компактные summaries без pagination в текущем controlled corpus; пагинация добавляется только после измеренного роста ответа.
- `NFR-003` Плеер/MediaReference — EPIC-009.
- `NFR-004` Переключатели Recording, Genre и LyricsVersion доступны с клавиатуры, отражают выбранное состояние и поддерживают back/forward.
- `NFR-005` На мобильном список Recording располагается над содержимым; правая колонка не создаёт горизонтальный overflow страницы.

## Acceptance criteria

1. Given seed Recording, when Visitor открывает `/recordings/{id}`, then видит `h1`, credits, жанры и ссылки на Works.
2. Given Work с одной Recording, then страница песни показывает её в центре без правой колонки.
3. Given Work с несколькими Recording, then справа видна хронология; выбор меняет центр и query без полной перезагрузки.
4. Given попытка published Recording без Work usage или primary credit, then публикация невозможна.
5. Given medley, then Recording содержит несколько упорядоченных Work usages, но её жанр не входит в фасеты Works-компонентов.
6. Given разные Genre Recording одного Work, then фасеты показывают distinct counts и фильтруют список.
7. Given самая ранняя Recording без origin Claim, then UI не называет её original.
8. Given разные supported origin Claims, then Recording получают разные точные бейджи.
9. Given несколько LyricsVersion, then язык меняет центральный текст без reload; machine translation не считается исполняемым.
10. Given `/`, then header содержит ссылку «Записи», а `/recordings` показывает публичный каталог.
11. Given неизвестный id, then безопасный not-found.
12. Given у выбранной Recording есть published ListeningGuide, then он виден и на странице Recording, и в её центральном блоке на странице песни.

## Данные и контракты

Recording, RecordingCredit, RecordingWorkUsage, RecordingLyricsUsage, ClassificationAssignment, origin Claims и составная song page projection. Public HTTP описан в [Data/API contract](data-api-workshop.md); OpenAPI обновляется до или вместе с реализацией.

## In scope

Страница записи, usages Works/lyrics, ссылки песня↔запись, жанровые фасеты, хронология, origin-бейджи, интерактивная Song page, seed и ListeningGuide empty/hide.

## Out of scope

Плеер, страница Track, Session/Take/Master aggregates, автоматическое распознавание covers, обязательное дерево Recording relations и pagination без измеренной необходимости.

## Ошибки и права

Как STORY-005. Отсутствие published Work usage или primary credit — ошибка публикации, не публичный 200. Draft/unpublished Work, LyricsVersion и Claims не раскрываются через составную страницу.

## Зависимости

STORY-007; STORY-005/006 для credits; EPIC-001 для Genre assignments; Historical Knowledge для origin Claims; [ADR-0007](../../../decisions/0007-musical-work-recording-and-origin-boundaries.md).

## Open questions

Блокирующих вопросов нет. OpenAPI wire schemas и конкретный router API обновляются до или вместе с реализацией.

## История изменений

- 2026-08-19: draft; Work обязателен; каталога нет.
- 2026-08-27: story принята; добавлены Work/Lyrics usages, жанровые фасеты, хронология без featured/original, origin Claims и интерактивное переключение на странице песни.
- 2026-08-28: по решению Product Owner добавлены глобальный каталог Recording и пункт header «Записи».
- 2026-08-30: по решению Product Owner ListeningGuide выбранной Recording также показывается в центральном блоке Song page.
