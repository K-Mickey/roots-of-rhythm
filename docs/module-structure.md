# Структура модулей и тестов

Статус: `accepted`

Документ фиксирует организационные границы кода без выбора языка, framework и окончательных имён source roots.

## Основной принцип

Каждый bounded context и supporting capability получает собственную верхнеуровневую подпапку. Тесты зеркалят эти границы. Это один repository, codebase и deployment unit; внутреннее взаимодействие остаётся прямым и не имитирует HTTP/RPC.

Концептуальная проекция:

```text
src/
├── people/
├── music/
├── dance/
├── historical_knowledge/
├── editorial/
├── discovery/
├── media/
├── ai_research/
└── entrypoints/
    ├── web_or_api/
    └── mcp/

tests/
├── people/
├── music/
├── dance/
├── historical_knowledge/
├── editorial/
├── discovery/
├── media/
├── ai_research/
├── entrypoints/
└── architecture/
```

`src` и конкретные названия адаптируются к выбранному стеку, но соответствие «модуль → отдельная подпапка → зеркальные тесты» сохраняется.

## Текущая Python-проекция

Backend содержит реально используемые общесистемные и предметные границы:

```text
backend/src/roots_of_rhythm/
├── config.py
├── entrypoints/
│   ├── api.py
│   ├── cli.py
│   └── dependencies.py
├── infrastructure/
│   ├── database.py
│   └── service_columns.py
├── seed/
│   ├── __init__.py
│   ├── corpus.py
│   └── runner.py
├── music_catalog/
│   ├── domain/
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── genre.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── errors.py
│   │   ├── genre_status_lookup.py
│   │   ├── ports.py
│   │   └── service.py
│   └── infrastructure/
│       ├── mapping.py
│       ├── models.py
│       ├── repository.py
│       └── unit_of_work.py
├── historical_knowledge/
│   ├── domain/
│   │   ├── claim.py
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── source.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── claim_service.py
│   │   ├── errors.py
│   │   ├── ports.py
│   │   └── source_service.py
│   └── infrastructure/
│       ├── mapping.py
│       ├── models.py
│       ├── repositories.py
│       └── unit_of_work.py
├── discovery/
│   ├── application/
│   │   ├── dto.py
│   │   ├── errors.py
│   │   ├── genre_overview.py
│   │   ├── genre_relation_projection.py
│   │   ├── genre_relations.py
│   │   └── genre_sources.py
│   └── presentation/
│       ├── schemas.py
│       └── genres.py
└── presentation/
    └── health.py

backend/tests/
├── entrypoints/
├── seed/
├── discovery/
│   ├── application/
│   └── fakes.py
├── music_catalog/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── fakes.py
└── historical_knowledge/
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── fakes.py
```

`entrypoints` собирает процессы и lifecycle (включая CLI `seed`), корневой `presentation` — health probes, `discovery` — public Genre overview, relations и sources read-side (queries + genres HTTP router), корневой `infrastructure` — общими runtime adapters (включая `ServiceColumnsMixin`), `seed` — controlled Genre corpus (Jazz–Swing–Jump Blues) через domain services, `config.py` — application settings. `music_catalog` владеет Genre/ClassificationConcept. `historical_knowledge` владеет GenreRelation Claim, Evidence references и Source/SourceVersion/SourceFragment stack с bibliographic metadata на Source и citation locator на Fragment; статус endpoint Genre читает через application port `GenreStatusLookup`, без импорта ORM Music Catalog. Persistence следует [ADR-0005](decisions/0005-persistence-service-columns-and-soft-delete.md): сервисные колонки на таблицах, soft-delete identity aggregates, hard rewrite owned evidence references. Будущие contexts не создаются пустыми: story добавляет верхнеуровневый module и только реально используемые подпапки.

## Внутренняя структура модуля

Создавать подпапку только когда в ней появляется реальный код:

```text
<module>/
├── domain/          # entities, value objects, policies
├── application/     # use cases, orchestration, owned ports
├── infrastructure/  # DB, SDK, filesystem and network adapters
└── presentation/    # только принадлежащий модулю transport mapping, если нужен
```

Не создавать четыре пустых слоя для простого модуля. Dependency direction важнее одинакового дерева директорий.

## Правила зависимостей

1. Domain не импортирует application, infrastructure, ORM, HTTP или SDK.
2. Application зависит от domain и определяет необходимые внешние ports.
3. Infrastructure реализует ports и может зависеть от framework/SDK.
4. Один модуль не импортирует ORM models, repositories или infrastructure другого.
5. Межмодульный вызов использует публичный application/query contract и стабильные IDs.
6. Media и AI Research не используют общую ORM session для изменения данных Core.
7. Entrypoint преобразует transport DTO и вызывает use case; доменные правила в transport не дублируются.
8. Общая папка `shared` не создаётся заранее. Код переносится туда только при нескольких реальных потребителях и отсутствии предметного владельца.

## Структура тестов

В папке каждого модуля находятся его unit и module-integration tests. Тесты внешних adapters остаются рядом с тестами владеющего модуля.

Отдельно:

- `tests/architecture` проверяет запрещённые imports и направление зависимостей;
- contract tests проверяют публичные application/port contracts на стороне владельца;
- end-to-end tests могут охватывать несколько модулей, но не заменяют локальные проверки;
- тестовые fixtures не становятся общим изменяемым доменным состоянием между модулями.

Точная test framework и команды определяются после выбора стека. Создание структуры не отменяет проектное правило: существующие тесты не изменяются без явного подтверждения пользователя.

## Будущее выделение

При запуске Media или AI Knowledge в отдельном process сначала переиспользуются их module/application boundaries и тесты. Сетевой contract, deployment и delivery tests добавляются только на этапе фактического выделения; заранее HTTP не имитируется.

Решение принято пользователем 2026-08-15.
