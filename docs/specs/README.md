# Спецификации

Текущий discovery-артефакт: [черновая карта epics](epic-map.md).

Первая формализуемая вертикаль:

- [EPIC-001: исследование жанра](epic-001-genre-exploration/README.md);
- [STORY-001: открыть опубликованную страницу Genre](epic-001-genre-exploration/story-001-view-published-genre/README.md) — `done`.
- [STORY-002: перейти между опубликованными Genre](epic-001-genre-exploration/story-002-navigate-published-genres/README.md) — `done`.
- [EPIC-002: исполнители, песни, записи и релизы](epic-002-performer-group-recording/README.md) — `draft`.
- [STORY-005: открыть опубликованного исполнителя](epic-002-performer-group-recording/story-005-view-published-performer/README.md) — `draft`.
- [STORY-006: открыть опубликованную группу](epic-002-performer-group-recording/story-006-view-published-group/README.md) — `draft`.
- [STORY-007: открыть опубликованную песню](epic-002-performer-group-recording/story-007-view-published-song/README.md) — `draft`.
- [STORY-008: открыть опубликованную запись](epic-002-performer-group-recording/story-008-view-published-recording/README.md) — `draft`.
- [STORY-009: открыть опубликованный релиз](epic-002-performer-group-recording/story-009-view-published-release/README.md) — `draft`.
- [STORY-010: показать связанные сущности на Genre](epic-002-performer-group-recording/story-010-genre-related-entities/README.md) — `draft`.
- [EPIC-010: точка входа, каталоги и поиск](epic-010-home-search-catalog/README.md) — `draft`.
- [Эволюция главной](epic-010-home-search-catalog/home-evolution.md) — `accepted`.
- [STORY-003: открыть минимальную главную](epic-010-home-search-catalog/story-003-minimal-home/README.md) — `done`.
- [STORY-004: открыть каталог опубликованных Genre](epic-010-home-search-catalog/story-004-published-genre-catalog/README.md) — `done`.
- [UI contract публичной страницы Genre](epic-001-genre-exploration/story-001-view-published-genre/ui.md) — `accepted`.
- [Data/API workshop публичной Genre page](epic-001-genre-exploration/story-001-view-published-genre/data-api-workshop.md) — `accepted`.
- [OpenAPI contract](../api/openapi.yaml) — `0.3.0`.
- [Декомпозиция STORY-001](epic-001-genre-exploration/story-001-view-published-genre/tasks.md) — `accepted`.
- [Декомпозиция STORY-002](epic-001-genre-exploration/story-002-navigate-published-genres/tasks.md) — `accepted`.
- [Декомпозиция STORY-003](epic-010-home-search-catalog/story-003-minimal-home/tasks.md) — `accepted`.
- [Приёмка STORY-001](epic-001-genre-exploration/story-001-view-published-genre/acceptance.md) — `accepted`.
- [Приёмка STORY-002](epic-001-genre-exploration/story-002-navigate-published-genres/acceptance.md) — `accepted`.
- [Приёмка STORY-003](epic-010-home-search-catalog/story-003-minimal-home/acceptance.md) — `accepted`.
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
