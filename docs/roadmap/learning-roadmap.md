# Учебная последовательность проекта

Статус: `accepted`

Цель последовательности — пройти SDD и DDD осознанно, а не использовать документацию как формальность. Каждый этап завершается проверяемым артефактом и отдельным решением о переходе дальше.

## 1. Product Discovery и Vision & Scope

Изучаем:

- проблему и пользовательскую ценность;
- персоны и системные роли;
- границы MVP;
- in scope и out of scope;
- открытые вопросы и риски.

Артефакты:

- `docs/product/vision.md`;
- `docs/product/mvp-scope.md`;
- `docs/product/personas-and-access.md`;
- `docs/product/open-questions.md`.

Состояние: видение принято; детали MVP остаются черновиком и уточняются параллельно с domain discovery.

## 2. Ubiquitous Language и Domain Discovery

Состояние: завершён. Workshops 001–004, ADR-0001–0003 и границы supporting capabilities приняты.

Изучаем:

- термины предметной области;
- различие entity, value object, aggregate и domain service;
- инварианты;
- ambiguous terms и контрпримеры;
- context mapping.

Артефакты:

- glossary;
- примеры и контрпримеры;
- context map;
- список агрегатов-кандидатов;
- domain risks.

## 3. Epics и первая User Story

Состояние: завершён для STORY-001. Epic, story, clarification, UI contract и актуальный OpenAPI `0.2.0` утверждены.

Изучаем:

- вертикальные срезы;
- FR, NFR и acceptance criteria;
- story mapping;
- трассировку требований;
- clarification.

Первая формализуемая story: одноязычная публичная страница Genre Swing с кратким определением, доступным историческим контекстом, объяснёнными Genre relations и видимым evidence status с источниками. Performer, Group, Recording, Dance-связи, локализация и переходы на другие detail pages рассматриваются последующими срезами.

## 4. Архитектурные решения

Состояние: application stack принят в ADR-0004; остаётся проверить готовность к декомпозиции и tracker bootstrap.

Изучаем:

- modular monolith;
- Clean Architecture;
- ports and adapters;
- repository и unit of work;
- CQRS-lite/read models;
- ADR и trade-off analysis.

Ожидаемые ADR:

- backend/frontend stack;
- modular monolith boundaries;
- PostgreSQL для графоподобных отношений;
- authentication;
- media provider abstraction принимается перед последним этапом MVP и не блокирует первую вертикаль;
- provenance и хранение RAG-источников.
- object storage, background jobs и эволюция search/vector infrastructure — только перед использующим этапом.

## Gate между архитектурой и реализацией: delivery workflow

До написания application code:

1. Подключить GitHub repository и создать GitHub Project.
2. Настроить минимальный workflow и milestone первой вертикали.
3. Перенести в tracker принятые epics/stories и только утверждённые результаты декомпозиции.
4. Связать issues с исходными документами `docs/specs/`; не копировать спецификации как независимый второй источник истины.
5. Зафиксировать правила синхронизации issue, pull request, specification и CI.

Артефакт: [Delivery workflow](delivery-workflow.md). Gate организационный: он должен быть выполнен перед реализацией STORY-001, но не меняет её продуктовый scope.

## 5. Первая вертикальная реализация

Проходим путь:

```text
PostgreSQL → repository → use case → HTTP API → React page
```

Реализация начинается только после утверждения story, API/UI-контрактов и необходимых ADR.

## 6. Editorial workflow

Изучаем:

- агрегаты и state machine;
- authorization;
- аудит;
- optimistic concurrency;
- draft/review/publish;
- внутренний UI.

## 7. Карта и read models

Изучаем:

- graph projection поверх PostgreSQL;
- query models;
- фильтры;
- визуализацию данных;
- accessibility альтернативы графу;
- производительность frontend.

## 8. RAG

Изучаем:

- ingestion и provenance;
- chunking;
- embeddings и retrieval;
- hybrid search при доказанной необходимости;
- citations;
- evaluation и grounded refusal.

## 9. MCP

Изучаем:

- tools, resources и prompts;
- stdio и Streamable HTTP;
- schemas;
- authentication и authorization;
- idempotency и audit для write-tools.

Начинаем с read-only MCP.

## 10. Agents

Изучаем:

- agent workflow;
- tool design;
- human-in-the-loop;
- critique and verification;
- structured outputs;
- agent evaluation;
- защита от автоматической публикации.

Сначала вручную реализуется редакционный процесс, затем он автоматизируется.

## 11. Музыкальные провайдеры и внешние интеграции

Завершающий этап MVP. До него страницы Recording работают без playback.

Изучаем:

- anti-corruption layer;
- provider adapters;
- external identity reconciliation;
- timeout, retry, rate limits и circuit breaker;
- graceful degradation;
- platform terms;
- региональную доступность;
- fallback от embed к внешней ссылке и к отсутствию playback.

Перед реализацией выполнить proof of concept на 20–30 стартовых Recording и принять ADR о наборе providers.

## 12. Production readiness

Изучаем:

- security review;
- observability;
- backup и restore;
- migrations;
- privacy и data retention;
- deployment и rollback;
- эксплуатационную документацию.

Работа оформляется в EPIC-012. Защита от abuse/DDoS и observability/alerts являются отдельными work items. Они не нужны для начала локальной разработки, но обязательны до публичного трафика в соответствии с этапностью EPIC-012.

## Правило перехода между этапами

Следующий этап начинается, когда:

- обязательные решения текущего этапа приняты;
- открытые блокирующие вопросы закрыты или явно вынесены из scope;
- документы согласованы;
- понятен проверяемый результат следующего этапа.
