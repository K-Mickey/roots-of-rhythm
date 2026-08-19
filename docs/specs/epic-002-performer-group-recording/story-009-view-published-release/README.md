# STORY-009: открыть опубликованный релиз

Статус: `draft`

Tracker: [GitHub issue #35](https://github.com/K-Mickey/roots-of-rhythm/issues/35).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть издание (альбом, сингл, EP): его историю, состав дорожек и связанные жанры и исполнителей.

## Проблема и измеримый результат

Релиз ≠ запись. Story успешна, если Visitor из header открывает `/releases` и страницу published Release с треклистом (номер + ссылка на Recording). На странице записи видны появления: релиз и номер дорожки.

## Контекст

Track — join Release↔Recording, владелец агрегата Release. Нет каталога Track. Related Performer/Group — списки. История/метаданные релиза — на этой странице. Seed дополняет записи STORY-008.

## Functional requirements

- `FR-001` `/releases` и `/releases/{id}` без авторизации.
- `FR-002` Каталог published релизов; имя — ссылка на `/releases/{id}`.
- `FR-003` Header «Релизы» → `/releases`.
- `FR-004` На `/` нет `/releases/{id}`.
- `FR-005` Страница: метаданные, история; пустые секции скрыты; жанры через assignment.
- `FR-006` Треклист: порядковый номер + ссылка на published Recording; Recording всегда указывает на свою песню (STORY-008).
- `FR-007` Страница записи показывает релизы, где она является Track.
- `FR-008` Seed: минимум один published Release с ≥1 Track на посеянную Recording.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` List/get без поиска/ES.
- `NFR-003` Полный каталог переизданий мира не цель; минимальный каталог продукта — да.

## Acceptance criteria

1. Given seed, when Visitor открывает `/releases`, then видит релиз как ссылку.
2. Given страница релиза, then трек ведёт на `/recordings/{id}`.
3. Given страница этой записи, then видна ссылка на релиз и номер дорожки.
4. Given header «Релизы», then `/releases`.
5. Given неизвестный id, then безопасный not-found.

## Данные и контракты

Release, Track, list/get; обновление recording page.

## In scope

Каталог, header, страница, треклист, seed.

## Out of scope

Страница Track; ReleaseCredit aggregate; label/producer как отдельные сущности.

## Ошибки и права

Как STORY-005.

## Зависимости

STORY-008.

## Open questions

Тип издания (альбом/сингл) как обязательное поле — Product Owner. Primary image — TBD.

## История изменений

- 2026-08-19: draft; минимальный каталог в этом epic.
