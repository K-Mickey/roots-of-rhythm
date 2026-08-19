# STORY-010: показать связанные сущности на Genre

Статус: `draft`

Tracker: [GitHub issue #36](https://github.com/K-Mickey/roots-of-rhythm/issues/36).

Epic: [EPIC-002](../README.md). Закрывает пункт 3 [EPIC-001](../../epic-001-genre-exploration/README.md).

## User story

Как Visitor на странице Genre, я хочу видеть связанных исполнителей, группы, песни, записи и релизы и перейти к ним.

## Проблема и измеримый результат

STORY-001 скрывает пустые секции Performer/Group/examples. Story успешна, если при наличии published связей Visitor видит имена как ссылки на существующие public routes. Нет отдельного каталога на Genre page.

## Контекст

ClassificationAssignment и связанные Recording/Work/Release. Не наследовать жанр автоматически. Seed явно связывает корпус EPIC-002 с Jazz/Swing/Jump Blues.

## Functional requirements

- `FR-001` Секции связанных published Performer, Group, MusicalWork, Recording, Release показываются, если не пусты; пустые по-прежнему скрыты.
- `FR-002` Имена — ссылки на `/performers/{id}`, `/groups/{id}`, `/songs/{id}`, `/recordings/{id}`, `/releases/{id}`.
- `FR-003` Непубличные объекты в секциях отсутствуют (как unpublished Genre в relations).
- `FR-004` Overview/relations/sources STORY-001/002 не ломаются.
- `FR-005` Seed: явные связи посеянных сущностей EPIC-002 с существующими Genre.

## Non-functional requirements

- `NFR-001` SSR.
- `NFR-002` Не вводить поиск на Genre page.
- `NFR-003` Dance/Story секции по-прежнему future empty/hidden.

## Acceptance criteria

1. Given seed связи, when Visitor открывает связанный Genre, then видит хотя бы один тип связанной сущности как `href`.
2. Given Genre без связанных Performer, then секция исполнителей скрыта.
3. Given клик по связанной песне, then `/songs/{id}`.
4. Given HTML без page JS, then `href` присутствуют.

## Данные и контракты

Genre page projections: связанные identity lists; seed assignments.

## In scope

Секции Genre page, seed links.

## Out of scope

Новые каталоги; карта; Dance/Story.

## Ошибки и права

Сбой секции — section error, не падение всей Genre page (как relations STORY-001).

## Зависимости

STORY-005–009.

## Open questions

Порядок секций на Genre page — уточнить в UI contract перед реализацией.

## История изменений

- 2026-08-19: draft из бывшего пункта 3 EPIC-001.
