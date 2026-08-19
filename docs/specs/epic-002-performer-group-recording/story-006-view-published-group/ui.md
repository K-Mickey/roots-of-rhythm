# UI contract: каталог и страница опубликованной группы

Статус: `accepted`

Story: [STORY-006](README.md).  
Shell: [design STORY-001](../../epic-001-genre-exploration/story-001-view-published-genre/design.md).

## Страница `/groups`

Landmarks: тот же `header` / `main` / `footer`.

`main`:

1. единственный `h1` — «Группы»;
2. список имён published Group; каждое имя — ссылка на `/groups/{id}`.

Доступное имя ссылки совпадает с отображаемым `name`. Ссылка визуально отличима от текста не только цветом (`underline="always"`, `c="pastel.7"`). Нет `href="#"`.

Пустой список: `h1` остаётся, пунктов нет, нет плейсхолдер-карточек и статистики.

Ошибка загрузки: `PageError`, `retryHref="/groups"`. Не использовать Genre/Performer/Group not-found.

## Страница `/groups/{id}`

Единственный `h1` — каноническое имя.

Опционально, если не пусто:

- aliases;
- описание;
- период существования Group (start и/или end; year + precision; клиент не выдумывает календарный день);
- список published Genre как ссылок на `/genres/{genre_id}` (порядок по имени жанра);
- участники: имя published Person — ссылка на `/performers/{id}`; рядом период membership и `roles_or_instruments`, если заданы; пустые period/roles не рендерятся;
- основное изображение (в этом срезе всегда отсутствует; тот же `PublicImage`, что Genre/Performer).

Пустые секции не рендерятся. Не публиковать Recording, editorial status, deleted, timestamps, evidence и provenance membership.

Ошибка overview API (не 404) — `PageError`. 404 и непубличный id — тот же not-found класс (`Материал не найден`).

## Header

Слева направо: project identity (`href="/"`), «Жанры» (`href="/genres"`), «Исполнители» (`href="/performers"`), «Группы» (`href="/groups"`). Ссылки на всех публичных страницах shell.

## Главная `/`

Без списка групп и без ссылок `/groups/{id}`. Header «Группы» допускается.

## Не входит

Поиск, фильтры, slug, Editorial UI, плеер, секции групп на Genre, страница Recording.
