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
├── application/
│   └── transaction.py               # общий transaction port
├── config.py
├── entrypoints/
│   ├── api.py
│   ├── cli.py
│   └── dependencies.py              # composition root API: transaction scope + repository factories
├── infrastructure/
│   ├── database.py
│   ├── service_columns.py
│   ├── transaction.py               # SqlAlchemyTransactionScope и привязка session
├── presentation/
│   └── health.py
├── seed/
│   ├── runner.py
│   ├── genre_knowledge.py
│   ├── people_and_groups.py
│   ├── musical_works.py
│   └── recording_corpus.py
├── text_lengths.py
├── people_catalog/
│   ├── domain/
│   ├── application/
│   │   ├── ports.py
│   │   ├── service.py               # lifecycle PersonService (registry UoW)
│   │   └── read_services/
│   ├── public/
│   │   └── published_person_reader.py
│   └── infrastructure/
│       ├── mapping.py
│       ├── models.py
│       ├── repository.py
│       └── unit_of_work.py
├── music_catalog/
│   ├── domain/
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── assignment.py
│   │   ├── genre.py
│   │   ├── group.py
│   │   ├── group_membership.py
│   │   ├── lyrics_version.py
│   │   ├── lyrics_version_credit.py
│   │   ├── lyrics_version_relation.py
│   │   ├── musical_work.py
│   │   ├── recording.py
│   │   ├── work_credit.py
│   │   ├── work_relation.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── errors.py
│   │   ├── ports.py
│   │   ├── *service.py             # lifecycle services (часть — registry UoW)
│   │   ├── read_services/          # Music context public readers
│   │   └── write_services/         # command use cases (Recording, ClassificationAssignment)
│   ├── public/                     # Genre, Group, Performer, SongList, SongOverview, Recording, RecordingLyrics readers
│   └── infrastructure/
│       ├── mapping/
│       ├── models/
│       ├── *repository.py
│       └── unit_of_work.py
├── historical_knowledge/
│   ├── domain/
│   │   ├── claim.py
│   │   ├── enums.py
│   │   ├── errors.py
│   │   ├── listening_guide.py
│   │   ├── recording_origin_claim.py
│   │   ├── source.py
│   │   └── value_objects.py
│   ├── application/
│   │   ├── errors.py
│   │   ├── ports/                  # claim/source/listening-guide repositories, UoW
│   │   ├── read_services/          # context readers
│   │   ├── services/               # lifecycle services
│   │   ├── write_services/         # command use cases (Claims, ListeningGuide)
│   │   └── source_service.py
│   ├── public/                     # GenreRelationClaim, RecordingKnowledge, SongContext, Source readers
│   └── infrastructure/
│       ├── mapping.py
│       ├── models/
│       ├── *repository.py
│       └── unit_of_work.py
└── discovery/
    ├── application/
    │   ├── queries/                # read use cases (GenreList, SongOverview, ...)
    │   ├── projections/            # чистые сборщики DTO
    │   ├── dto/
    │   └── errors/
    └── presentation/
        ├── schemas.py
        ├── genres.py
        ├── performers.py
        ├── groups.py
        ├── songs.py
        └── recordings.py
```

`entrypoints` собирает процессы и lifecycle (включая CLI `seed`), корневой `presentation` — health probes, `discovery` — public Genre, Performer, Group, Song и Recording read-side, корневой `infrastructure` — общими runtime adapters (включая `ServiceColumnsMixin` и `SqlAlchemyTransactionScope`), `seed` — controlled Genre, Performer/Group, MusicalWork и Recording corpus через domain/application services, `config.py` — application settings. `application.transaction` — общий transaction port. `people_catalog` владеет Person. `music_catalog` владеет Genre/ClassificationConcept, ClassificationAssignment, Group, MusicalWork, LyricsVersion и Recording. `historical_knowledge` владеет GenreRelation Claim, RecordingOrigin Claim, ListeningGuide, Evidence references и Source/SourceVersion/SourceFragment stack; create/publish Claims используют transaction-only boundary и отдельно внедрённые repositories одной PostgreSQL session. Persistence следует [ADR-0005](decisions/0005-persistence-service-columns-and-soft-delete.md): сервисные колонки на таблицах, soft-delete identity aggregates, hard rewrite owned evidence references. Будущие contexts не создаются пустыми: story добавляет верхнеуровневый module и только реально используемые подпапки.

Тесты зеркалят те же границы, плюс общие helpers:

```text
backend/tests/
├── entrypoints/          # HTTP-уровень и интеграция с API
├── seed/                 # corpus seeds против PostgreSQL
├── architecture/         # static AST checks импортных границ (R1–R4)
├── discovery/            # query/projection readers и их fakes
├── music_catalog/        # domain/application/infrastructure музыкального контекста
├── historical_knowledge/ # domain/application/infrastructure исторического контекста
├── people_catalog/       # domain/application/infrastructure People
└── support/              # общие transaction scopes и PostgreSQL helpers
```

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
