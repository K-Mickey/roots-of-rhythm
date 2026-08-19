# STORY-005: открыть опубликованного исполнителя

Статус: `draft`

Tracker: [GitHub issue #31](https://github.com/K-Mickey/roots-of-rhythm/issues/31).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть список опубликованных исполнителей и страницу одного из них, чтобы узнать, кто это, без заранее известного UUID.

## Проблема и измеримый результат

Сейчас public identity есть только у Genre. Story успешна, если анонимный Visitor из header открывает `/performers`, видит published Performer и переходит на `/performers/{id}`.

## Контекст

Публичная страница — музыкальное представление Person, не вторая идентичность. Каталог минимальный (id + name), как STORY-004. Поиск/фильтры — EPIC-010. Каждая story дополняет seed.

## Functional requirements

- `FR-001` Visitor открывает `/performers` и `/performers/{id}` без авторизации.
- `FR-002` Каталог показывает только published, не удалённые Performer; порядок по каноническому имени; пустой список — успех.
- `FR-003` Имя в каталоге — ссылка на `/performers/{id}`.
- `FR-004` Header содержит «Исполнители» → `/performers`; identity → `/`; «Жанры» сохраняется.
- `FR-005` На `/` нет списка исполнителей и ссылок `/performers/{id}`.
- `FR-006` Страница показывает имя и доступный обзор (био/контекст, жанры); пустые секции скрыты.
- `FR-007` Непубличный id даёт тот же класс not-found, что Genre, без утечки существования.
- `FR-008` Seed дополняется минимум одним published Performer.

## Non-functional requirements

- `NFR-001` SSR: имена каталога и страница читаются без обязательного page JS.
- `NFR-002` Публичный list + get API без Elasticsearch, auth, очереди, графа.
- `NFR-003` Нет поиска, фильтров, slug, Editorial UI, плеера.

## Acceptance criteria

1. Given приложение, when Visitor открывает `/performers`, then виден заголовок каталога и published имена как ссылки.
2. Given seed, when Visitor активирует имя, then открывается страница с `h1` этого исполнителя.
3. Given header, when Visitor активирует «Исполнители», then открывается `/performers`.
4. Given `/`, when Visitor смотрит главную, then нет `/performers/{id}`.
5. Given неизвестный id, when открывается `/performers/{id}`, then безопасный not-found.
6. Given сбой list API, when открывается `/performers`, then page error, не Genre not-found.

## Данные и контракты

- OpenAPI: list/get published Performer (`id`, `name` в list; обзор на get);
- routes `/performers`, `/performers/{id}`;
- header;
- seed increment.

## In scope

Каталог, header, страница, seed, People Catalog persistence, Discovery read.

## Out of scope

Group/Recording/Work/Release pages; influence graph CQ-003 целиком; timeline карьеры.

## Ошибки и права

Visitor не авторизуется. Draft/archived неотличимы от отсутствия.

## Зависимости

STORY-004 `done`.

## Open questions

- Конкретные имена seed — Product Owner.
- Обязательность primary image — [open-questions](../../../product/open-questions.md) #2.
- Минимум полей публикации Performer кроме имени — Product Owner.

## История изменений

- 2026-08-19: draft; каталог и header сразу для проверки.
