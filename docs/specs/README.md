# Спецификации

Текущий discovery-артефакт: [черновая карта epics](epic-map.md).

Первая формализуемая вертикаль:

- [EPIC-001: исследование жанра](epic-001-genre-exploration/README.md);
- [STORY-001: открыть опубликованную страницу Genre](epic-001-genre-exploration/story-001-view-published-genre/README.md) — `done`.
- [UI contract публичной страницы Genre](epic-001-genre-exploration/story-001-view-published-genre/ui.md) — `accepted`.
- [Data/API workshop публичной Genre page](epic-001-genre-exploration/story-001-view-published-genre/data-api-workshop.md) — `accepted`.
- [OpenAPI contract](../api/openapi.yaml) — `0.2.0`.
- [Декомпозиция STORY-001](epic-001-genre-exploration/story-001-view-published-genre/tasks.md) — `accepted`.
- [Приёмка STORY-001](epic-001-genre-exploration/story-001-view-published-genre/acceptance.md) — `accepted`.
- [EPIC-012: production readiness](epic-012-production-readiness/README.md) — `draft`; не блокирует локальную реализацию, обязательные work items блокируют публичный трафик.

Каждая story хранится в отдельной директории и содержит цель, контекст, FR, NFR, критерии приёмки, границы, ошибки, зависимости и открытые вопросы.

Рекомендуемая структура:

```text
docs/specs/<epic>/<story>/
  README.md
  api.md
  ui.md
  tasks.md
```

Не начинать нетривиальную реализацию, пока обязательные требования не определены или пользователь явно не разрешил прототипирование.
