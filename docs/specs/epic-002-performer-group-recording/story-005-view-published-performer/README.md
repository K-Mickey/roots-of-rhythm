# STORY-005: открыть опубликованного исполнителя

Статус: `done`

Tracker: [GitHub issue #31](https://github.com/K-Mickey/roots-of-rhythm/issues/31).

Epic: [EPIC-002](../README.md).

## User story

Как Visitor, я хочу открыть список опубликованных исполнителей и страницу одного из них, чтобы узнать, кто это, без заранее известного UUID.

## Проблема и измеримый результат

Сейчас public identity есть только у Genre. Story успешна, если анонимный Visitor из header открывает `/performers`, видит published Performer и переходит на `/performers/{id}`.

## Контекст

Публичная страница — музыкальное представление Person, не вторая идентичность. Каталог минимальный (id + name), как STORY-004. Поиск/фильтры — EPIC-010. Каждая story дополняет seed.

Person хранит каноническое имя, aliases, biography, birth/death с точностью года и external identities. Публикация Person по-прежнему требует только каноническое имя; остальные content-поля и ClassificationAssignment опциональны. Пустые секции скрыты. Основное изображение не обязательно и в этом срезе не загружается (`primary_image` всегда `null`). Seed — 1–3 исполнителя на Jazz / Swing / Jump Blues плюс «проходной» Louis Armstrong.

Одинаковые канонические имена допустимы; дедупликация по aliases и external identities — отдельный use case, не глобальный unique index имени.

## Functional requirements

- `FR-001` Visitor открывает `/performers` и `/performers/{id}` без авторизации.
- `FR-002` Каталог показывает только published, не удалённые Performer; порядок по каноническому имени; пустой список — успех.
- `FR-003` Имя в каталоге — ссылка на `/performers/{id}`.
- `FR-004` Header содержит «Исполнители» → `/performers`; identity → `/`; «Жанры» сохраняется.
- `FR-005` На `/` нет списка исполнителей и ссылок `/performers/{id}`.
- `FR-006` Страница показывает имя и доступный обзор: aliases, биография, даты жизни, external identities, published жанры через ClassificationAssignment; пустые секции скрыты. Внутренние `editorial_status`, deleted и timestamps не публичны.
- `FR-007` Непубличный id даёт тот же класс not-found, что Genre, без утечки существования.
- `FR-008` Seed дополняется published Performer: Charlie Parker (Jazz); Count Basie и Benny Goodman (Swing); Louis Jordan и Big Joe Turner (Jump Blues); Louis Armstrong (Jazz и Swing).

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
7. Given overview с заполненными aliases, биографией, датами или identities, when Visitor открывает страницу, then эти поля видны; пустые не рендерятся.
8. Given ClassificationAssignment без explanation/claim, provenance или unpublished Person/Genre, when Editor публикует assignment, then публикация отклоняется.

## Данные и контракты

- OpenAPI `0.5.0`: list published Performer (`id`, `name`); get — все публичные Person content-поля плюс `primary_image` и `genres`;
- [UI](ui.md), [Data/API](data-api-workshop.md);
- routes `/performers`, `/performers/{id}`;
- header;
- seed increment.

## In scope

Каталог, header, страница, seed, People Catalog persistence, ClassificationAssignment для жанров на странице исполнителя, Discovery read.

## Out of scope

Group/Recording/Work/Release pages; связанные сущности на странице Genre (STORY-010); influence graph CQ-003 целиком; timeline карьеры; MediaAsset upload; публичный UI provenance/evidence assignment; evidence references для `supported`/`disputed` assignment.

## Ошибки и права

Visitor не авторизуется. Draft/archived неотличимы от отсутствия.

## Зависимости

STORY-004 `done`.

## Open questions

Нет. Product Owner 2026-08-19 закрыл имена seed, публикацию по имени и опциональное изображение. Уточнение 2026-08-19: полный Person content на get; assignment — explanation или claim_id, provenance, evidence_status; до evidence references публикуется только `unverified`.

## История изменений

- 2026-08-20: Product Owner закрыл приёмку; STORY-005 переведена в `done`.
- 2026-08-19: Person content (aliases, dates, identities) на public get; публикация Person по-прежнему только по имени; ClassificationAssignment — explanation или claim, provenance, evidence_status.
- 2026-08-19: принята; seed-имена, публикация по имени, скрытие пустых секций и опциональный image.
- 2026-08-19: draft; каталог и header сразу для проверки.
