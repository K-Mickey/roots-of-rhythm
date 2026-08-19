# UI contract: каталог опубликованных Genre

Статус: `accepted`

Story: [STORY-004](README.md).  
Shell: [design STORY-001](../../epic-001-genre-exploration/story-001-view-published-genre/design.md).  
Ссылки на Genre: [STORY-002 ui.md](../../epic-001-genre-exploration/story-002-navigate-published-genres/ui.md).

## Страница `/genres`

Landmarks: тот же `header` / `main` / `footer`.

`main`:

1. единственный `h1` — «Жанры»;
2. список имён published Genre; каждое имя — ссылка на `/genres/{genre_id}`.

Доступное имя ссылки совпадает с отображаемым `name`. Ссылка визуально отличима от текста не только цветом (`underline="always"`, `c="pastel.7"`), как имя related Genre в STORY-002. Нет `href="#"`.

Пустой список: `h1` остаётся, пунктов нет, нет плейсхолдер-карточек и статистики.

Ошибка загрузки: тот же безопасный page-error паттерн, что у Genre overview (`PageError`), `retryHref="/genres"`. Не использовать Genre not-found.

## Header

Слева направо: project identity (`href="/"`), затем ссылка «Жанры» (`href="/genres"`). Слот не остаётся пустым: «Жанры» рендерится на всех публичных страницах shell.

## Главная `/`

Без изменений STORY-003: нет списка Genre и нет ссылок `/genres/{id}`. Header «Жанры» на `/genres` допускается.

## Не входит

Поиск, фильтры, карточки с definition, пагинация, slug, изменение Genre detail layout.
