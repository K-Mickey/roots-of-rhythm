# STORY-007: открыть опубликованную песню

Статус: `draft`

Tracker: [GitHub issue #33](https://github.com/K-Mickey/roots-of-rhythm/issues/33).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть песню как отдельную сущность: что это за произведение, жанр, текст, исполнители — и позже её записи.

## Проблема и измеримый результат

MusicalWork в UI — **Песня**, не запись и не альбом. Story успешна, если Visitor из header открывает `/songs` и страницу published песни. Секция записей и «послушать» скрыты, пока нет STORY-008.

## Контекст

Домен: MusicalWork. URL: `/songs`, `/songs/{id}`. Текст песни на странице; пустой скрыт. Исполнители — related-список, не WorkCredit. Жанр — ClassificationAssignment. Сравнение каверов не входит.

## Functional requirements

- `FR-001` `/songs` и `/songs/{id}` без авторизации.
- `FR-002` Каталог published песен (id + name); ссылки на `/songs/{id}`.
- `FR-003` Header «Песни» → `/songs`.
- `FR-004` На `/` нет `/songs/{id}`.
- `FR-005` Страница: имя, доступные подробности, жанры, текст если есть, related Performer/Group как ссылки на опубликованные.
- `FR-006` Секции записей и «послушать» скрыты, пока нет published Recording этой песни.
- `FR-007` Пустые прочие секции скрыты.
- `FR-008` Seed: минимум одна published песня; запись не обязательна.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` List/get без ES/auth. Плеер не вводится.
- `NFR-003` Переводы текста и аннотации сверх одного текста — не в этой story (один опциональный текст).

## Acceptance criteria

1. Given seed, when Visitor открывает `/songs`, then видит имя песни как ссылку.
2. Given header «Песни», then `/songs`.
3. Given страница песни без записей, then нет секции записей и нет блока «послушать».
4. Given `/`, then нет `/songs/{id}`.
5. Given неизвестный id, then безопасный not-found.

## Данные и контракты

MusicalWork; ClassificationAssignment; related lists; seed.

## In scope

Каталог, header, страница песни, опциональный текст, seed.

## Out of scope

Recording pages; плеер; compare covers; авторы как отдельный credit aggregate.

## Ошибки и права

Как STORY-005.

## Зависимости

STORY-005, STORY-006 (для related ссылок; жанры — EPIC-001).

## Open questions

- Обязателен ли текст для публикации песни? Предложение: нет. Минимум полей кроме имени — Product Owner.
- Featured-запись для «послушать» при нескольких записях — решается в STORY-008.

## История изменений

- 2026-08-19: draft; текст на странице; записи появятся в STORY-008.
