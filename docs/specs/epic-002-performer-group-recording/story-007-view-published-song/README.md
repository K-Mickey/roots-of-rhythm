# STORY-007: открыть опубликованную песню

Статус: `accepted`

Tracker: [GitHub issue #33](https://github.com/K-Mickey/roots-of-rhythm/issues/33).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть песню как авторское произведение: узнать её названия, авторов, тексты, подтверждённую классификацию и связи с производными произведениями — а после STORY-008 исследовать её записи.

## Проблема и измеримый результат

MusicalWork в UI — **Песня**, не запись, исполнитель или альбом. Story успешна, если Visitor из header открывает `/songs` и страницу published Work с авторами, доступными версиями текста и производными Works. Песня публикуется без текста и Recording; их отсутствие не заполняется фиктивными данными.

## Контекст

Домен: MusicalWork, WorkCredit, WorkRelation, LyricsVersion и LyricsVersionRelation. URL: `/songs`, `/songs/{id}`. Авторы принадлежат WorkCredit; исполнители появятся только через RecordingCredit в STORY-008. Классификация Work независима от жанров Recording. Полный текст опционален и выдаётся только при разрешающей rights/access policy Source.

## Functional requirements

- `FR-001` `/songs` и `/songs/{id}` без авторизации.
- `FR-002` Каталог published песен (id + name); ссылки на `/songs/{id}`.
- `FR-003` Header «Песни» → `/songs`.
- `FR-004` На `/` нет `/songs/{id}`.
- `FR-005` Страница: имя, aliases, доступные подробности, опубликованные WorkCredit, независимая классификация Work, производные WorkRelation и опубликованные LyricsVersion; пустые секции скрыты.
- `FR-006` Секции записей и «послушать» скрыты, пока нет published Recording этой песни.
- `FR-007` Пустые прочие секции скрыты.
- `FR-008` Controlled seed содержит Sixteen Tons, One O'Clock Jump, Ornithology, Sing, Sing, Sing (With a Swing), Shake, Rattle and Roll и West End Blues; Recording и полный текст не обязательны.
- `FR-009` Публикация MusicalWork требует canonical title и provenance, но не требует WorkCredit, LyricsVersion, ClassificationAssignment или Recording.
- `FR-010` LyricsVersion использует BCP 47 language tag и назначение `performable | reading_translation`; машинный перевод может быть только `reading_translation` и не публикуется без review.
- `FR-011` Исполняемый перевод, новые авторские слова, адаптация и независимо воспроизводимая опубликованная аранжировка оформляются производным Work с доказательной WorkRelation.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` List/get без ES/auth. Плеер не вводится.
- `NFR-003` Количество авторов, языков, LyricsVersion и связанных Works не ограничивается фиксированным product maximum.
- `NFR-004` Страница не загружает и не моделирует Recording до STORY-008.

## Acceptance criteria

1. Given seed, when Visitor открывает `/songs`, then видит имя песни как ссылку.
2. Given header «Песни», then `/songs`.
3. Given страница песни без записей, then нет секции записей и нет блока «послушать».
4. Given `/`, then нет `/songs/{id}`.
5. Given неизвестный id, then безопасный not-found.
6. Given published Work без текста и credits, when Visitor открывает страницу, then получает 200 без пустых секций.
7. Given published credits и производный Work, then видны авторы и направленная ссылка с типом relation.
8. Given несколько published LyricsVersion, then видны доступные языки; версия с недоступным по rights policy телом его не раскрывает.
9. Given machine translation, then она помечена как машинная и не считается исполняемой.

## Данные и контракты

MusicalWork, WorkCredit, WorkRelation, LyricsVersion, LyricsVersionRelation, ClassificationAssignment и seed. Public HTTP описан в [Data/API contract](data-api-workshop.md); OpenAPI обновляется до или вместе с реализацией.

## In scope

Каталог, header, страница песни, credits, производные Works, несколько версий текста, независимая классификация Work и seed.

## Out of scope

Recording persistence/pages, RecordingWorkUsage, жанровые фасеты исполнений, origin Claims, плеер, Session/Take/Master и Editorial UI.

## Ошибки и права

Как STORY-005. Тело LyricsVersion выдаётся только при разрешающей rights/access policy Source; отсутствие права не делает Work непубличным.

## Зависимости

STORY-005 и STORY-006 для публичных Person/Group links; EPIC-001 для ClassificationAssignment; [ADR-0007](../../../decisions/0007-musical-work-recording-and-origin-boundaries.md).

## Open questions

Блокирующих вопросов нет. OpenAPI wire schemas обновляются до или вместе с реализацией API.

## История изменений

- 2026-08-28: прогон TASK-007 записан в [acceptance.md](acceptance.md) (`draft` до утверждения Product Owner).
- 2026-08-19: draft; текст на странице; записи появятся в STORY-008.
- 2026-08-27: story принята; добавлены WorkCredit, производные Works и несколько rights-aware LyricsVersion; текст и Recording необязательны.
