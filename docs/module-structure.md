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
│   ├── service_columns.py
│   └── write_scopes.py
├── seed/
│   ├── __init__.py
│   ├── corpus.py
│   └── runner.py
├── people_catalog/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── music_catalog/
│   ├── domain/
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── assignment.py
│   │   ├── genre.py
│   │   ├── group.py
│   │   ├── group_membership.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── errors.py
│   │   ├── assignment_service.py
│   │   ├── group_membership_service.py
│   │   ├── group_service.py
│   │   ├── ports.py
│   │   └── service.py
│   └── infrastructure/
│       ├── mapping.py
│       ├── models.py
│       ├── assignment_repository.py
│       ├── group_membership_repository.py
│       ├── group_repository.py
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
│   │   ├── errors.py
│   │   ├── ports/
│   │   ├── services/
│   │   ├── use_cases/
│   │   └── source_service.py
│   ├── public/
│   │   └── genre_relation_claim_reader.py
│   └── infrastructure/
│       ├── claim_repository.py
│       ├── genre_relation_claim_reader.py
│       ├── mapping.py
│       ├── models.py
│       ├── source_repository.py
│       └── unit_of_work.py
├── discovery/
│   ├── application/
│   │   ├── dto.py
│   │   ├── errors.py
│   │   ├── genre_overview.py
│   │   ├── genre_list.py
│   │   ├── genre_relation_projection.py
│   │   ├── genre_relations.py
│   │   ├── genre_sources.py
│   │   ├── group_list.py
│   │   ├── group_overview.py
│   │   ├── performer_list.py
│   │   └── performer_overview.py
│   └── presentation/
│       ├── schemas.py
│       ├── genres.py
│       ├── groups.py
│       └── performers.py
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

`entrypoints` собирает процессы и lifecycle (включая CLI `seed`), корневой `presentation` — health probes, `discovery` — public Genre, Performer и Group read-side, корневой `infrastructure` — общими runtime adapters (включая `ServiceColumnsMixin`), `seed` — controlled Genre, Performer и Group corpus через domain services, `config.py` — application settings. `people_catalog` владеет Person. `music_catalog` владеет Genre/ClassificationConcept и ClassificationAssignment. `historical_knowledge` владеет GenreRelation Claim, Evidence references и Source/SourceVersion/SourceFragment stack с bibliographic metadata на Source и citation locator на Fragment; create/publish Claim используют transaction-only boundary и отдельно внедрённые repositories одной PostgreSQL session. Persistence следует [ADR-0005](decisions/0005-persistence-service-columns-and-soft-delete.md): сервисные колонки на таблицах, soft-delete identity aggregates, hard rewrite owned evidence references. Будущие contexts не создаются пустыми: story добавляет верхнеуровневый module и только реально используемые подпапки.

## Внутренняя структура модуля

Создавать подпапку только когда в ней появляется реальный код:

```text
<module>/
├── domain/          # entities, value objects, policies
├── application/     # cohesive services, use cases, read contracts, owned ports
├── infrastructure/  # DB, SDK, filesystem and network adapters
└── presentation/    # только принадлежащий модулю transport mapping, если нужен
```

Не создавать четыре пустых слоя для простого модуля. Dependency direction важнее одинакового дерева директорий.

Application service может группировать связный lifecycle одного aggregate. Отдельный command use case нужен при самостоятельном сценарии или отличающихся зависимостях, правах и транзакции; отдельный класс на каждый тривиальный метод не требуется. Discovery query является read use case и зависит от публичных context readers, а не от ORM другого модуля. Mapper/projector остаётся обычной функцией, если отдельный объект не даёт самостоятельной пользы. Подробности: [ADR-0008](decisions/0008-application-operations-read-contracts-and-transactions.md).

## Правила зависимостей

1. Domain не импортирует application, infrastructure, ORM, HTTP или SDK.
2. Application зависит от domain и определяет необходимые внешние ports.
3. Infrastructure реализует ports и может зависеть от framework/SDK.
4. Один модуль не импортирует ORM models, repositories или infrastructure другого.
5. Межмодульный вызов использует публичный application/query contract и стабильные IDs.
6. Media и AI Research не используют общую ORM session для изменения данных Core.
7. Entrypoint преобразует transport DTO и вызывает use case; доменные правила в transport не дублируются.
8. Общая папка `shared` не создаётся заранее. Код переносится туда только при нескольких реальных потребителях и отсутствии предметного владельца.
9. UoW определяет write-транзакцию, а operation получает используемые repositories отдельно; существующие registry-style UoW мигрируют инкрементально.
10. Public reader читает и оптимизирует только данные владеющего context; межконтекстную публичную видимость вычисляет Discovery.

## Структура тестов

В папке каждого модуля находятся его unit и module-integration tests. Тесты внешних adapters остаются рядом с тестами владеющего модуля.

Отдельно:

- `tests/architecture` проверяет запрещённые imports и направление зависимостей;
- contract tests проверяют публичные application/port contracts на стороне владельца;
- end-to-end tests могут охватывать несколько модулей, но не заменяют локальные проверки;
- тестовые fixtures не становятся общим изменяемым доменным состоянием между модулями;
- повторяющиеся builders (published Genre, Claim) и integration `engine`/seed cleanup выносятся в module-local `conftest`/builders или `tests/support` по [STORY-002 TASK-001](specs/epic-001-genre-exploration/story-002-navigate-published-genres/tasks.md), без новых test-фреймворков.

Точная test framework и команды определяются после выбора стека. Создание структуры не отменяет проектное правило: существующие тесты не изменяются без явного подтверждения пользователя.

## Будущее выделение

При запуске Media или AI Knowledge в отдельном process сначала переиспользуются их module/application boundaries и тесты. Сетевой contract, deployment и delivery tests добавляются только на этапе фактического выделения; заранее HTTP не имитируется.

Решение принято пользователем 2026-08-15.
