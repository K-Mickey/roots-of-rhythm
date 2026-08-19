# UI contract: каталог и страница опубликованного исполнителя

Статус: `accepted`

Story: [STORY-005](README.md).  
Shell: [design STORY-001](../../epic-001-genre-exploration/story-001-view-published-genre/design.md).

## Страница `/performers`

Landmarks: тот же `header` / `main` / `footer`.

`main`:

1. единственный `h1` — «Исполнители»;
2. список имён published Performer; каждое имя — ссылка на `/performers/{id}`.

Доступное имя ссылки совпадает с отображаемым `name`. Ссылка визуально отличима от текста не только цветом (`underline="always"`, `c="pastel.7"`). Нет `href="#"`.

Пустой список: `h1` остаётся, пунктов нет, нет плейсхолдер-карточек и статистики.

Ошибка загрузки: `PageError`, `retryHref="/performers"`. Не использовать Genre not-found и Performer not-found.

## Страница `/performers/{id}`

Единственный `h1` — каноническое имя.

Опционально, если не пусто:

- aliases;
- биографический обзор;
- дата рождения и/или смерти (year + precision; клиент не выдумывает полный календарный день);
- external identities: при наличии `url` — ссылка; без `url` — текст `provider` и `identifier`;
- список published Genre как ссылок на `/genres/{genre_id}` (порядок по имени жанра);
- основное изображение (в этом срезе всегда отсутствует; non-null контракт `PublicImage` поддерживается той же безопасной отрисовкой, что Genre).

Пустые секции не рендерятся. Не публиковать Group membership, Recording credits, timeline, editorial status, deleted и timestamps. Provenance и evidence assignment на странице не показываются.

Ошибка overview API (не 404) — `PageError`. 404 и непубличный id — тот же not-found класс, что Genre (`Материал не найден`).

## Header

Слева направо: project identity (`href="/"`), «Жанры» (`href="/genres"`), «Исполнители» (`href="/performers"`). Ссылки на всех публичных страницах shell.

## Главная `/`

Без изменений STORY-003: нет списка исполнителей и нет ссылок `/performers/{id}`. Header «Исполнители» допускается.

## Не входит

Поиск, фильтры, slug, Editorial UI, плеер, секции связанных исполнителей на Genre.
