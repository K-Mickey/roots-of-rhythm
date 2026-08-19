# STORY-002: перейти между опубликованными Genre

Статус: `accepted`

Tracker: [GitHub issue #23](https://github.com/K-Mickey/roots-of-rhythm/issues/23).

Epic: [EPIC-001](../README.md).

## User story

Как Visitor, я хочу открыть связанный опубликованный Genre со страницы текущего, чтобы продолжить чтение истории переходов, не запоминая identity и не возвращаясь к внешнему списку.

## Проблема и измеримый результат

После STORY-001 Jazz и Jump Blues уже имеют тот же public route `/genres/{genre_id}`, но имена в relations остаются текстом (STORY-001 `FR-010` / `AC-8`). Story успешна, если Visitor со страницы Swing по рабочей ссылке попадает на опубликованный связанный Genre и обратно, а непубличные объекты по-прежнему неотличимы от «не найдено».

## Контекст

Это узкое снятие ограничения STORY-001, а не каталог и не главная. Главная и identity-link на `/` входят в [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md) ([EPIC-010](../../epic-010-home-search-catalog/README.md)).

Публичный relations response уже содержит identity связанного Genre. Новый list endpoint для этой story не нужен.

## Functional requirements

- `FR-001` Visitor может без авторизации перейти с карточки опубликованной relation на публичную страницу связанного Genre.
- `FR-002` Ссылка использует тот же public route и identity, что STORY-001: `/genres/{genre_id}`.
- `FR-003` Ссылкой является только имя связанного Genre. Label типа связи, explanation, temporal/geographic context, evidence status и Source references ссылками не становятся.
- `FR-004` Ссылка — обычный HTML navigation (`<a href>`), читаемый без обязательного client-side JavaScript.
- `FR-005` Непубличный, архивный или неизвестный Genre по-прежнему даёт тот же публичный not-found, что STORY-001. Relations API не отдаёт связанные unpublished Genre; отдельного «битого» link state для них нет.
- `FR-006` Поведение overview, relations и sources projections, empty/error states и evidence labels STORY-001 не меняется, кроме замены текстового имени на ссылку.

## Non-functional requirements

- `NFR-001` Client-side переход использует уже принятый loading skeleton STORY-001; первая загрузка целевой страницы остаётся SSR.
- `NFR-002` Не добавляются slug, prefetch, граф, поиск, очередь, кэш или отдельный сервис.
- `NFR-003` Доступность имени как ссылки не зависит только от цвета: focus/hover/underline или эквивалентный textual affordance обязательны.

## Acceptance criteria

1. Given открыта страница Swing с опубликованной relation на Jazz, when Visitor активирует имя Jazz, then открывается публичная страница Jazz с её `name` и `definition`.
2. Given открыта страница Swing с relation на Jump Blues, when Visitor активирует имя Jump Blues, then открывается публичная страница Jump Blues.
3. Given открыта страница Jazz, when Visitor активирует имя связанного Swing в обратной перспективе, then открывается публичная страница Swing.
4. Given карточка relation, when Visitor просматривает её, then тип связи, explanation и evidence block не являются ссылками на Genre.
5. Given HTML без выполнения page JavaScript, when запрашивается страница Swing, then имя связанного Genre присутствует как `href` на `/genres/{id}`.
6. Given неизвестный `genre_id` в URL после перехода, when Visitor открывает его, then показывается тот же not-found, что в STORY-001, без раскрытия, существовал ли объект.

## Данные и контракты в области изменения

- UI Genre relations: имя связанного Genre становится ссылкой;
- [UI contract STORY-001](../story-001-view-published-genre/ui.md) в части «имя не ссылка»;
- Playwright/Vitest ожидания разметки relations;
- OpenAPI не меняется.

## In scope

- ссылки на существующие public Genre pages из relations;
- сохранение perspective labels и evidence presentation.

## Out of scope

- главная, header identity `/`, каталог, поиск, карта;
- slug/SEO URLs;
- хлебные крошки и история просмотра;
- Performer/Group/Recording links;
- новый API list/search;
- локализация.

## Ошибки и права

- Visitor читает только опубликованное.
- Ссылка ведёт только на identity из публичного relations response.
- Сбой overview/relations/sources на целевой странице остаётся по правилам STORY-001.

## Зависимости

- [STORY-001](../story-001-view-published-genre/README.md) — `done`;
- публичные operations overview/relations/sources;
- параллельно, но не блокирует: [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md).

## Open questions

Нет блокирующих. Порядок элементов на главной относится к [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md) и не содержит список Genre.

## История изменений

- 2026-08-19: черновик по решению Product Owner продолжить EPIC-001 навигацией между опубликованными Genre.
- 2026-08-19: Product Owner утвердил story и декомпозицию.
