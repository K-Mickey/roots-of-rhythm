# STORY-006: открыть опубликованную группу

Статус: `accepted`

Tracker: [GitHub issue #32](https://github.com/K-Mickey/roots-of-rhythm/issues/32).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть каталог групп и страницу группы, чтобы отличить коллектив от исполнителя.

## Проблема и измеримый результат

Group — отдельная идентичность. Story успешна, если Visitor из header открывает `/groups` и страницу published Group с участниками-ссылками на Performer, когда они опубликованы.

## Контекст

Не смешивать с Performer. Membership не доказывает credit на все Recording. Seed дополняет корпус STORY-005.

Поля Group и GroupMembership взяты из [workshop 004](../../../domain/workshops/004-aggregate-boundaries.md), [workshop 001](../../../domain/workshops/001-relationships-and-observations.md) и [domain-overview](../../../domain/domain-overview.md). В этом срезе не вводится справочник инструментов: `roles_or_instruments` — строки. Даты публичного API — уже принятый `TemporalBound` (year + precision Genre/Person), без day/month. `evidence[]` и provenance membership хранятся, на публичной странице не показываются.

## Functional requirements

- `FR-001` `/groups` и `/groups/{id}` без авторизации.
- `FR-002` Каталог: published Group, порядок по каноническому имени; имя — ссылка на `/groups/{id}`.
- `FR-003` Header «Группы» → `/groups`.
- `FR-004` На `/` нет `/groups/{id}`.
- `FR-005` Страница показывает каноническое имя и доступный обзор Group: aliases, описание, период существования, published жанры, `primary_image`; пустые секции скрыты. Внутренние editorial_status, deleted и timestamps не публичны.
- `FR-006` Известные **published** GroupMembership с **published** Person: имя — ссылка на `/performers/{id}`; если есть период и/или роли/инструменты — они видны. Unpublished Person и unpublished membership в публичный список не входят (без отдельного leak).
- `FR-007` Recording на странице группы нет до STORY-008.
- `FR-008` Seed: четыре published Group и membership на seed Performer STORY-005; публикация Group не требует состава.

## Non-functional requirements

- `NFR-001` SSR без обязательного page JS.
- `NFR-002` List/get API без поиска/ES/auth.
- `NFR-003` Полная реконструкция всех составов и вычисляемые ярлыки вроде «поздний период» не требуются. Известные who/when/what на membership хранятся и показываются.

## Acceptance criteria

1. Given seed, when Visitor открывает `/groups`, then видит published Group как ссылки.
2. Given header «Группы», when активирует, then `/groups`.
3. Given страница Group с published membership на seed Performer, when смотрит участников, then имя — `href` на `/performers/{id}`; период и роли видны, если заданы.
4. Given `/`, then нет `/groups/{id}`.
5. Given неизвестный id, then безопасный not-found.
6. Given Group без membership, when Editor публикует Group, then публикация не отклоняется из-за пустого состава.
7. Given сбой list API, when открывается `/groups`, then page error, не Group not-found.

## Данные и контракты

- OpenAPI `0.6.0`: list/get Group;
- [UI](ui.md), [Data/API](data-api-workshop.md);
- routes `/groups`, `/groups/{id}`;
- header;
- seed increment.

### Group (Music Catalog)

Хранится: canonical name; aliases; description; period start/end (`TemporalBound`, граница может быть пустой); editorial status; soft-delete. Публикация требует только canonical name. Одинаковые имена допустимы.

Публичный get: `id`, `name`, `aliases`, `description`, `period` `{ start, end }` (оба nullable), `primary_image` (в срезе всегда `null`), `genres`, `members`.

### GroupMembership (отдельный aggregate)

Хранится (domain-overview):

- performer (PersonId), group (GroupId) — обязательны;
- period start/end — optional;
- `roles_or_instruments[]` — optional строки, не enum и не catalog;
- evidence[], provenance, editorial_status — не публичны в этой story.

Публичный member: `{ id, name, period, roles_or_instruments }` только если membership и Person published.

## In scope

Каталог, header, страница, membership (кто/когда/на чём), seed, ClassificationAssignment Group→Genre, Discovery read.

## Out of scope

Страницы Recording/Work/Release; related на Genre (STORY-010); Editorial UI; поиск; instrument catalog; evidence/provenance UI; карта всех исторических составов.

## Ошибки и права

Как STORY-005. `GROUP_NOT_FOUND`, то же сообщение «Материал не найден.»

## Зависимости

STORY-005 `done`.

## Open questions

Нет. Product Owner 2026-08-20: seed четыре группы в Jazz/Swing/Jump Blues; image как у Performer; публикация без полного состава; membership хранит период и роли/инструменты.

## История изменений

- 2026-08-20: принята; поля Group/Membership сверены с workshop; seed 4 групп; декомпозиция TASK-001–004.
- 2026-08-19: draft; каталог и header сразу.
