# UI contract: ссылки на связанный Genre

Статус: `accepted`

Story: [STORY-002](README.md).  
Базовый contract: [STORY-001 ui.md](../story-001-view-published-genre/ui.md).

## Изменение относительно STORY-001

В карточке relation имя связанного Genre — ссылка на `/genres/{genre_id}`.

- доступное имя ссылки совпадает с отображаемым `name`;
- ссылка визуально отличима от окружающего текста не только цветом;
- нет `href="#"`, `role="link"` без URL и hover без реального перехода;
- остальной текст карточки не становится ссылкой.

Not-found и page error не меняются этой story. Ссылка «на главную» добавляется в [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md).

## Не входит

Каталог, поиск, карта, slug, prefetch, изменение layout relations.
