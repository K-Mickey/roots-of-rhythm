# UI contract: минимальная главная

Статус: `accepted`

Story: [STORY-003](README.md).  
Shell: [design STORY-001](../../epic-001-genre-exploration/story-001-view-published-genre/design.md).

## Страница `/`

Landmarks: тот же `header` / `main` / `footer`. Primary nav не рендерится.

`main` — одна центрированная группа:

1. крупный `h1` — имя продукта;
2. короткое описание (vision) сразу под ним.

Нет списка Genre, статистики, пустых nav-пунктов будущих разделов.

Вертикальное и горизонтальное центрирование в доступной области `main` (под header, над footer). На узком viewport текст остаётся читаемым, без обрезки `h1`.

## Header identity

`href="/"` вместо `#`.

## Not-found Genre

Ссылка «На главную» на `/`.

## Не входит

Каталог жанров, тема/spacing tokens заново, тёмная тема.
