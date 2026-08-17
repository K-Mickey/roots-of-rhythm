# Аудит покрытия черновых epics — 2026-08-16

Статус: `research`

Проверяемое утверждение: черновая epic map покрывает пользовательские результаты MVP и core questions, не превращая архитектурные слои и инфраструктуру в отдельные epics.

## Найденные пробелы

### Главная, каталоги и единый поиск

Факт: MVP требует минималистичную главную, статистику, списки Genre/Performer/Group/Dance и единый поиск. Исходная карта не назначала им epic.

Сценарий отказа: detail pages существуют, но Visitor не имеет точки входа и должен знать URL заранее.

Исправление: добавлен EPIC-010 «Найти точку входа и нужный материал».

### Stories были объединены с картой

Факт: Story является редакционным документом с секциями, Claims и примерами; карта является интерактивной Discovery projection с accessibility-альтернативой.

Сценарий отказа: одна epic содержит два независимых UI, разные модели редактирования и разные критерии готовности.

Исправление: EPIC-003 оставлен картой, EPIC-011 выделен для Stories/сравнений/маршрутов.

## Существенные уточнения

### MCP имел скрытую зависимость от RAG

Read-only search/get tools могут использовать опубликованные query contracts до RAG. Только `ask_published_corpus` зависит от EPIC-006. Зависимость разделена.

### Первая Genre story ссылалась на ещё не созданные pages

На момент аудита Performer/Recording предлагались как компактные примеры без detail links. Последующим продуктовым решением от 2026-08-16 они полностью исключены из STORY-001. Первый срез содержит только Genre, Genre relations и empty states будущих секций; это ещё надёжнее исключает broken links и лишние зависимости от EPIC-002.

### Editorial слишком велик для одной story, но допустим как epic

EPIC-005 объединяет одну пользовательскую цель Editor, однако позже требует вертикальной декомпозиции: access, draft creation, review/publish, source management и studio queue не должны стать одной story.

## Что намеренно не стало epic

- S3, previews, vector database, search engine, worker, queue и event bus — технические задачи/ADR внутри stories;
- authentication — часть Editor journey;
- MediaAsset — сквозная возможность страниц и Editorial, а не самостоятельная ценность MVP;
- отдельные services Media/AI/Discovery — deployment evolution, а не product epic;
- MusicalWork/Release pages, галереи, монетизация и расширенный Dance domain — deferred scope.

## Coverage verdict

После добавления EPIC-010/011 карта покрывает все явно заявленные публичные и служебные страницы MVP, CQ-001–CQ-007, RAG, MCP, agent workflow и завершающую provider integration.

Остаются продуктовые решения, а не пропущенные epics: стартовый набор жанров, обязательность изображений, editorial permissions, story types, source rights и RAG quality gates. Локализация, fallback и локализованные URL удалены из EPIC-001 последующим решением Product Owner и перенесены в deferred scope.

## Рекомендация devil's advocate

Принять расширенную epic map как основу discussion, но не формализовать все epics сразу. Сначала подтвердить EPIC-001 и границы первой story; остальные epics формализовать перед их discovery, сохраняя IDs и coverage matrix.
