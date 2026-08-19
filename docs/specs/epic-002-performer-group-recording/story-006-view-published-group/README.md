# STORY-006: открыть опубликованную группу

Статус: `draft`

Tracker: [GitHub issue #32](https://github.com/K-Mickey/roots-of-rhythm/issues/32).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть каталог групп и страницу группы, чтобы отличить коллектив от исполнителя.

## Проблема и измеримый результат

Group — отдельная идентичность. Story успешна, если Visitor из header открывает `/groups` и страницу published Group с участниками-ссылками на Performer, когда они опубликованы.

## Контекст

Не смешивать с Performer. Membership не доказывает credit на все Recording. Seed дополняет корпус STORY-005.

## Functional requirements

- `FR-001` `/groups` и `/groups/{id}` без авторизации.
- `FR-002` Каталог: published Group, порядок по имени; имя — ссылка на `/groups/{id}`.
- `FR-003` Header «Группы» → `/groups`.
- `FR-004` На `/` нет `/groups/{id}`.
- `FR-005` Страница: название, период, описание, жанры; пустые секции скрыты.
- `FR-006` Известные участники — ссылки на published Performer; unpublished не ссылки и не отличаются от отсутствия отдельным leak.
- `FR-007` Recording на странице группы скрыты или текст без ссылок до STORY-008.
- `FR-008` Seed: минимум одна published Group и membership.

## Non-functional requirements

- `NFR-001` SSR без обязательного page JS.
- `NFR-002` List/get API без поиска/ES/auth.
- `NFR-003` Полная реконструкция состава по периодам не требуется.

## Acceptance criteria

1. Given seed, when Visitor открывает `/groups`, then видит published Group как ссылки.
2. Given header «Группы», when активирует, then `/groups`.
3. Given страница Group с membership на seed Performer, when смотрит участников, then имя — `href` на `/performers/{id}`.
4. Given `/`, then нет `/groups/{id}`.
5. Given неизвестный id, then безопасный not-found.

## Данные и контракты

List/get Group; GroupMembership; seed.

## In scope

Каталог, header, страница, membership links, seed.

## Out of scope

Страницы Recording/Work/Release; Editorial; поиск.

## Ошибки и права

Как STORY-005.

## Зависимости

STORY-005.

## Open questions

Имена seed Group — Product Owner. Primary image — TBD.

## История изменений

- 2026-08-19: draft; каталог и header сразу.
