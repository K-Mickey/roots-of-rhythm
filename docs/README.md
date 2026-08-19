# Документация Swing Music Story

Проект развивается по Spec-Driven Development. Документы имеют явный статус:

- `accepted` — решение согласовано и является текущей основой;
- `done` — принятые требования выполнены, приёмка закрыта;
- `draft` — рабочее предложение, требующее отдельного согласования;
- `research` — результаты исследования без автоматического принятия решения;
- `TBD` — вопрос не решён, владелец решения указан в документе.

## Навигация

- [Видение продукта](product/vision.md)
- [Ключевые вопросы продукта](product/core-questions.md)
- [Будущие возможности](product/future-scope.md)
- [Границы MVP](product/mvp-scope.md)
- [Аудитория, роли и редактура](product/personas-and-access.md)
- [Открытые продуктовые вопросы](product/open-questions.md)
- [Черновая доменная модель](domain/domain-overview.md)
- [Границы Editorial, Discovery и AI Research](domain/supporting-capabilities.md)
- [Media Management, файлы и streaming integrations](domain/media-management.md)
- [Глоссарий предметной области](domain/glossary.md)
- [Политика музыкальной классификации](domain/classification-policy.md)
- [DDD Workshop 001: язык связей и наблюдений](domain/workshops/001-relationships-and-observations.md)
- [DDD Workshop 002: связь танца и музыки](domain/workshops/002-dance-music-relations.md)
- [DDD Workshop 003: Context Map и владельцы правил](domain/workshops/003-context-map.md)
- [DDD Workshop 004: агрегаты, инварианты и транзакции](domain/workshops/004-aggregate-boundaries.md)
- [DDD Workshop 005: публикация и публичная видимость](domain/workshops/005-publication-and-visibility.md)
- [RAG, MCP и агенты](ai/ai-scope.md)
- [Исследование музыкальных провайдеров](research/media-providers.md)
- [Исследование источников музыкальной классификации](research/music-classification-sources.md)
- [Исследование связей танца и музыки](research/dance-music-relations.md)
- [Исследование подходов к локализации](research/localization-approaches.md)
- [Исследование Genre relations первого seed](research/seed-genre-relations.md)
- [Аудит согласованности архитектурных решений](research/architecture-consistency-audit-2026-08-15.md)
- [Аудит покрытия epics](research/epic-coverage-audit-2026-08-16.md)
- [Development, deployment и operations stack](research/development-deployment-operations-stack.md)
- [Учебная последовательность](roadmap/learning-roadmap.md)
- [GitHub delivery workflow](roadmap/delivery-workflow.md)
- [Эволюция инфраструктуры](roadmap/infrastructure-evolution.md)
- [Архитектура](architecture.md)
- [Структура модулей и тестов](module-structure.md)
- [Разработка](development.md)
- [Спецификации](specs/README.md)
- [Черновая карта epics](specs/epic-map.md)
- [EPIC-001: исследование жанра](specs/epic-001-genre-exploration/README.md)
- [EPIC-002: исполнители, песни, записи и релизы](specs/epic-002-performer-group-recording/README.md) — `draft`
- [EPIC-010: точка входа, каталоги и поиск](specs/epic-010-home-search-catalog/README.md) — `draft`
- [Эволюция главной HOME-0/1/2](specs/epic-010-home-search-catalog/home-evolution.md) — `accepted`
- [EPIC-012: production readiness](specs/epic-012-production-readiness/README.md)
- [STORY-001: открыть опубликованную страницу Genre](specs/epic-001-genre-exploration/story-001-view-published-genre/README.md) — `done`
- [UI contract публичной страницы Genre](specs/epic-001-genre-exploration/story-001-view-published-genre/ui.md) — `accepted`
- [UI/design specification shell и Genre page](specs/epic-001-genre-exploration/story-001-view-published-genre/design.md) — `accepted`
- [Data/API workshop публичной Genre page](specs/epic-001-genre-exploration/story-001-view-published-genre/data-api-workshop.md) — `accepted`
- [Декомпозиция STORY-001](specs/epic-001-genre-exploration/story-001-view-published-genre/tasks.md) — `accepted`
- [Декомпозиция STORY-002](specs/epic-001-genre-exploration/story-002-navigate-published-genres/tasks.md) — `accepted`
- [Декомпозиция STORY-003](specs/epic-010-home-search-catalog/story-003-minimal-home/tasks.md) — `accepted`
- [Приёмка STORY-001 (TASK-009)](specs/epic-001-genre-exploration/story-001-view-published-genre/acceptance.md) — `accepted`
- [Приёмка STORY-002 (TASK-003)](specs/epic-001-genre-exploration/story-002-navigate-published-genres/acceptance.md) — `accepted`
- [Приёмка STORY-003 (TASK-002)](specs/epic-010-home-search-catalog/story-003-minimal-home/acceptance.md) — `accepted`
- [STORY-002: перейти между опубликованными Genre](specs/epic-001-genre-exploration/story-002-navigate-published-genres/README.md) — `done`
- [STORY-003: открыть минимальную главную](specs/epic-010-home-search-catalog/story-003-minimal-home/README.md) — `done`
- [STORY-004: открыть каталог опубликованных Genre](specs/epic-010-home-search-catalog/story-004-published-genre-catalog/README.md) — `done`
- [STORY-005: открыть опубликованного исполнителя](specs/epic-002-performer-group-recording/story-005-view-published-performer/README.md) — `draft`
- [STORY-006: открыть опубликованную группу](specs/epic-002-performer-group-recording/story-006-view-published-group/README.md) — `draft`
- [STORY-007: открыть опубликованную песню](specs/epic-002-performer-group-recording/story-007-view-published-song/README.md) — `draft`
- [STORY-008: открыть опубликованную запись](specs/epic-002-performer-group-recording/story-008-view-published-recording/README.md) — `draft`
- [STORY-009: открыть опубликованный релиз](specs/epic-002-performer-group-recording/story-009-view-published-release/README.md) — `draft`
- [STORY-010: показать связанные сущности на Genre](specs/epic-002-performer-group-recording/story-010-genre-related-entities/README.md) — `draft`
- [OpenAPI contract](api/openapi.yaml) — `0.3.0`
- [API-контракты](api/README.md)
- [ADR](decisions/README.md)
- [ADR-0004: application stack первой вертикали](decisions/0004-application-stack.md) — `accepted`
- [ADR-0005: сервисные колонки persistence и soft-delete](decisions/0005-persistence-service-columns-and-soft-delete.md) — `proposed`

## SDD-последовательность

```text
Discovery → Vision & Scope → Ubiquitous Language → Context Map
→ Epics → User Stories → Clarification → API/UI contracts
→ ADR → Tasks → Implementation → Verification
```

Не переводить черновик в `accepted` и не начинать реализацию только потому, что документ существует.
