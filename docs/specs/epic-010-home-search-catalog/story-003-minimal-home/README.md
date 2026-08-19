# STORY-003: открыть минимальную главную

Статус: `done`

Tracker: [GitHub issue #24](https://github.com/K-Mickey/roots-of-rhythm/issues/24).

Epic: [EPIC-010](../README.md).  
Стадия главной: [HOME-0](../home-evolution.md).

## User story

Как Visitor, я хочу открыть главную и сразу понять, что это за продукт, без каталога и без заранее известного Genre ID.

## Проблема и измеримый результат

Сейчас точка входа — прямой URL Genre или header stub `#`. Story успешна, если анонимный Visitor открывает `/` и видит крупное название и короткое описание по центру, без списка жанров, статистики и чужих разделов.

## Контекст

Главная — EPIC-010, не EPIC-001. Product Owner 2026-08-19: HOME-0 без дашборда и **без жанров на главной**; ориентир по жанрам будет на отдельной странице каталога (следующая story EPIC-010, не этот срез).

Навигация relation → Genre — [STORY-002](../../epic-001-genre-exploration/story-002-navigate-published-genres/README.md); независима.

## Functional requirements

- `FR-001` Visitor открывает `/` без авторизации.
- `FR-002` В центре экрана крупное имя продукта `Roots of Rhythm` и слоган: «История музыки для тех кто танцует и слушает».
- `FR-003` На главной нет списка Genre, карточек жанров, счётчиков, `HomeStatistics`, поиска и ссылок на Performer, Group, Recording, Dance, Stories, карту, studio.
- `FR-004` Header project identity ведёт на `/` (снимается stub `href="#"` STORY-001).
- `FR-005` Публичный not-found Genre содержит ссылку на главную `/`.

## Non-functional requirements

- `NFR-001` Первая загрузка `/` содержательно доступна без обязательного client-side JavaScript.
- `NFR-002` Не требуются новый public API, Elasticsearch, кэш, очередь, графовая БД, authentication.
- `NFR-003` Текст главной статичен (имя продукта и слоган FR-002); CMS и i18n не вводятся.

## Acceptance criteria

1. Given запущенное приложение, when Visitor открывает `/` без авторизации, then в центре экрана видны крупное имя продукта и слоган из FR-002.
2. Given seed Jazz, Swing и Jump Blues, when Visitor смотрит `/`, then на странице нет имён жанров как навигации и нет ссылок `/genres/{id}`.
3. Given `/`, when просматривается HTML, then нет секции статистики и нет чисел корпуса как дашборда.
4. Given header любой публичной страницы, when Visitor активирует project identity, then открывается `/`.
5. Given not-found Genre, when Visitor ищет путь назад, then доступна ссылка на `/`.
6. Given HTML без page JavaScript, when запрашивается `/`, then название и описание присутствуют в документе.

## Данные и контракты в области изменения

- frontend route `/` и layout главной;
- shell identity;
- not-found Genre;
- [design stub `#`](../../epic-001-genre-exploration/story-001-view-published-genre/design.md).

Публичный OpenAPI не меняется. List/каталог Genre — отдельная будущая story EPIC-010.

## In scope

- HOME-0: центрированные title + description;
- identity `/` и ссылка домой с not-found.

## Out of scope

- страница со всеми жанрами;
- HOME-1/HOME-2;
- `HomeStatistics` и любой list API;
- поиск, карта, slug, локализация, Editorial UI.

## Ошибки и права

- Visitor не авторизуется.
- Статический текст не подменяется ошибкой API: backend для этой страницы не вызывается.

## Зависимости

- STORY-001 `done` (shell);
- [home-evolution.md](../home-evolution.md).

## Open questions

Нет. Product Owner 2026-08-19: жанры на главной не нужны; достаточно крупного названия и короткого описания по центру.

## История изменений

- 2026-08-19: черновик HOME-0 с list Genre.
- 2026-08-19: Product Owner убрал жанры с главной; story принята как центрированные title + description.
- 2026-08-19: Product Owner зафиксировал слоган главной: «История музыки для тех кто танцует и слушает».
- 2026-08-19: прогон TASK-002 записан в [acceptance.md](acceptance.md) (`draft` до утверждения Product Owner).
- 2026-08-19: Product Owner закрыл приёмку; STORY-003 переведена в `done`.
