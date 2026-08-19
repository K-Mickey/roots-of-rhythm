# Архитектура Swing Music Story

Статус: `draft`.

## Принятая основа

Система начинается как модульный монолит с одним deployment unit, одной реляционной БД и синхронными application-вызовами. Инфраструктурный event bus, микросервисы и отдельные database schemas не используются без измеренной необходимости.

Принятые bounded contexts:

- People Catalog;
- Music Catalog;
- Dance Catalog;
- Historical Knowledge.

Historical Knowledge владеет Claims и историческими связями и ссылается на стабильные IDs остальных contexts. Context изменяет только принадлежащие ему данные; межконтекстные операции оркестрируются application layer.

Первая фактическая предметная проекция — Python package `music_catalog`. Его domain содержит immutable Genre/ClassificationConcept и ClassificationAssignment, application — команды и принадлежащие ему Repository/Unit of Work contracts, infrastructure — отдельную SQLAlchemy persistence model и PostgreSQL adapters. ORM models и sessions не выходят из infrastructure; transport DTO не переиспользуют domain entities.

Вторая проекция — `historical_knowledge`: GenreRelation Claim с Evidence references и Source/SourceVersion/SourceFragment aggregates. Source хранит bibliographic metadata (title, author, responsible organization, publication, publication date, canonical external URL); SourceFragment хранит citation locator. Публикация Claim проверяет published endpoint Genre через тот же command scope, что и Historical Knowledge (`knowledge_music_scope`: два UoW, одна PostgreSQL session); публичная видимость relation пересчитывается на чтении.

Третья проекция — `people_catalog`: Person (публичная страница исполнителя — Discovery-представление Person). Discovery отдаёт public Genre и Performer projections.

Editorial, Discovery и AI Research планируются как логические supporting capabilities, но не как bounded contexts или сервисы. Editorial оркестрирует редакционный lifecycle, Discovery является read side, AI Research владеет только техническими индексами, AI-запусками и proposals. Их физические code/module boundaries не фиксируются до использующей story.

## Принятый application stack

- backend: Python, Litestar, msgspec и Uvicorn;
- persistence: PostgreSQL, SQLAlchemy 2.x, Alembic и Psycopg 3 async; таблицы несут сервисные колонки `created_at`/`updated_at`/`deleted`, soft-delete identity aggregates и hard rewrite owned links — [ADR-0005](decisions/0005-persistence-service-columns-and-soft-delete.md); write-path identity aggregates использует `SELECT … FOR UPDATE` — [ADR-0006](decisions/0006-pessimistic-write-locks.md);
- frontend: React, TypeScript, Next.js App Router и Mantine-first design system;
- contract boundary: OpenAPI 3.1 и generated TypeScript types;
- dependency/tooling baseline: uv, pnpm, Ruff, mypy, ESLint, Prettier, pytest, Vitest, React Testing Library и небольшой critical Playwright suite.

Next.js и Litestar запускаются как два process одного координируемого application release. Backend остаётся единственным modular monolith; frontend не владеет domain data и не обращается к PostgreSQL. Детали и компромиссы: [ADR-0004](decisions/0004-application-stack.md).

Принятые границы: [границы supporting capabilities](domain/supporting-capabilities.md). Решение и альтернативы: [ADR-0001](decisions/0001-modular-monolith-context-boundaries.md). Подробный Context Map: [DDD Workshop 003](domain/workshops/003-context-map.md).

## Подготовка к возможному выделению

Принят extraction-ready modular monolith: сильные кандидаты располагаются на краю приложения и зависят от application-owned ports, но остаются в одном codebase и deployment unit.

Сильные кандидаты: единый Media Service и единый AI Knowledge Service. Media объединяет storage, image processing и streaming provider integrations, но не хранит музыкальное аудио. AI Knowledge объединяет ingestion, embeddings, retrieval, RAG и agents. Discovery/Search является условным третьим кандидатом. MCP и REST остаются entrypoints. Доменные contexts и Editorial не проектируются как будущие сервисы без отдельной operational причины.

Не создавать remote-shaped interface для каждого внутреннего вызова. Между contexts достаточно явных in-process application contracts, стабильных IDs и запрета передавать ORM models. Порт вводится при реальной внешней или заменяемой границе либо утверждённом кандидате на отдельный процесс.

Решение и альтернативы: [ADR-0003](decisions/0003-extraction-ready-monolith.md). Подробный план: [эволюция инфраструктуры](roadmap/infrastructure-evolution.md). Media boundary: [Media Management](domain/media-management.md). Обязательная проекция каталогов и тестов: [структура модулей](module-structure.md).

## Осознанные ограничения

- нет infrastructure event bus;
- нет generic Entity aggregate;
- нет отдельных Media, Search или Provider bounded contexts;
- нет Elasticsearch или графовой БД без измеренной потребности;
- aggregate и transaction boundaries приняты в [DDD Workshop 004](domain/workshops/004-aggregate-boundaries.md) и [ADR-0002](decisions/0002-aggregate-and-transaction-boundaries.md).

## TBD

Зафиксировать здесь после утверждения:

- authentication и authorization;
- deployment topology;
- language-specific package names остальных bounded contexts;
- инфраструктурная стратегия после выбора backend/database stack;
- внешние интеграции.

Не добавлять предполагаемые компоненты до принятия решения.
