# STORY-004: открыть каталог опубликованных Genre

Статус: `done`

Tracker: [GitHub issue #30](https://github.com/K-Mickey/roots-of-rhythm/issues/30).

Epic: [EPIC-010](../README.md).  
Стадия главной: [HOME-0](../home-evolution.md) не меняется на `/`.

## User story

Как Visitor, я хочу открыть список всех опубликованных жанров и перейти на нужную страницу Genre, не зная UUID заранее.

## Проблема и измеримый результат

После HOME-0 точка входа понятна, но ориентир по жанрам отсутствует: Visitor всё ещё должен знать `/genres/{id}`. Story успешна, если анонимный Visitor из header открывает `/genres`, видит все published Genre и по имени попадает на существующую страницу Genre.

## Контекст

Это story 2 EPIC-010: отдельная страница каталога, не список на главной. Product Owner 2026-08-19: вход — ссылка «Жанры» в header; на `/` имён жанров нет.

Страница Genre и переходы relation → Genre — [STORY-001](../../epic-001-genre-exploration/story-001-view-published-genre/README.md) и [STORY-002](../../epic-001-genre-exploration/story-002-navigate-published-genres/README.md).

## Functional requirements

- `FR-001` Visitor открывает `/genres` без авторизации.
- `FR-002` Страница показывает все published, не удалённые Genre; draft и archived отсутствуют.
- `FR-003` Каждое имя — ссылка на `/genres/{genre_id}` (тот же public route, что STORY-001/002).
- `FR-004` Порядок имён стабилен по каноническому имени.
- `FR-005` Header содержит ссылку «Жанры» на `/genres`; project identity по-прежнему ведёт на `/`.
- `FR-006` На главной `/` нет списка Genre и нет ссылок `/genres/{id}` (HOME-0).
- `FR-007` Пустой корпус: страница каталога доступна, список пуст, без фейковых карточек.
- `FR-008` Ошибка list API не маскируется под not-found Genre; Visitor видит безопасное сообщение и может повторить загрузку `/genres`.

## Non-functional requirements

- `NFR-001` Первая загрузка `/genres` содержательно доступна без обязательного client-side JavaScript (имена присутствуют как `href` в HTML).
- `NFR-002` Публичный `GET /api/v1/genres` без Elasticsearch, кэша, очереди, графовой БД и authentication.
- `NFR-003` Поиск, фильтры, пагинация, slug и карточки с definition не входят в этот срез.

## Acceptance criteria

1. Given запущенное приложение, when Visitor открывает `/genres` без авторизации, then виден заголовок каталога и published Genre как ссылки на `/genres/{id}`.
2. Given seed Jazz, Swing и Jump Blues, when Visitor смотрит `/genres`, then три имени присутствуют в порядке Jazz, Jump Blues, Swing и ведут на соответствующие id.
3. Given `/genres`, when Visitor активирует имя Jazz, then открывается страница Jazz с `h1` Jazz.
4. Given header любой публичной страницы, when Visitor активирует «Жанры», then открывается `/genres`.
5. Given seed корпус, when Visitor смотрит `/`, then нет ссылок `/genres/{id}` и нет имён жанров как навигации по каталогу; identity ведёт на `/`.
6. Given HTML без page JavaScript, when запрашивается `/genres` при непустом корпусе, then имена Genre присутствуют как `href` на `/genres/{id}`.
7. Given сбой `GET /api/v1/genres`, when Visitor открывает `/genres`, then страница не является Genre not-found; показано безопасное сообщение без внутренних деталей.

## Данные и контракты в области изменения

- [OpenAPI](../../../api/openapi.yaml) `GET /api/v1/genres` (`GenreListResponse`);
- frontend route `/genres` и header;
- Discovery list query и `GenreRepository.list_published`.

## In scope

- публичный list published Genre (`id`, `name`);
- страница `/genres`;
- ссылка «Жанры» в header.

## Out of scope

- список жанров на `/`;
- HOME-1/HOME-2, `HomeStatistics`;
- поиск, фильтры, пагинация, slug;
- каталоги Performer, Group, Recording, Dance, Stories;
- Editorial UI.

## Ошибки и права

- Visitor не авторизуется.
- Непубличные Genre неотличимы от отсутствия в списке.
- Сбой чтения списка — ошибка страницы каталога, не `GENRE_NOT_FOUND`.

## Зависимости

- STORY-001 и STORY-002 `done`;
- STORY-003 `done` (HOME-0).

## Open questions

Нет. Product Owner 2026-08-19: каталог — `/genres`; вход только из header.

## История изменений

- 2026-08-19: story принята как финальный каталог published Genre, не временный список на главной.
- 2026-08-19: реализация и проверки закрыты; STORY-004 переведена в `done` ([#30](https://github.com/K-Mickey/roots-of-rhythm/issues/30)).
