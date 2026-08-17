# ADR-0003: монолит с подготовленными границами выделения

Статус: `accepted`

Дата: 2026-08-15.

## Контекст

Проект стартует модульным монолитом, но в будущем изображения, ingestion, embeddings, retrieval и внешние интеграции могут потребовать отдельных процессов и инфраструктуры. Если они будут напрямую использовать ORM-модели, общую session и транзакции доменных contexts, позднее выделение станет дорогим.

Если, напротив, заранее имитировать сеть между всеми модулями, проект получит DTO mapping, ошибки доставки и абстракции без текущей операционной пользы.

## Решение

Использовать extraction-ready modular monolith:

- сильные кандидаты на отдельный process располагаются на инфраструктурном краю монолита;
- внешний или заменяемый механизм скрывается за портом, принадлежащим использующему application layer;
- порт описывает возможность, а не API SDK или будущий сетевой протокол;
- ORM models, DB session и прямые writes не пересекают подготовленную границу;
- операции сильного кандидата не создают новый инвариант общей транзакции с доменным context;
- повторяемые workflows используют стабильные IDs и idempotency только когда такой workflow реально появляется;
- внутренние bounded contexts используют in-process application contracts без искусственного HTTP/RPC.

### Текущая проекция внутри монолита

```text
Core Application
├── People Catalog
├── Music Catalog
├── Dance Catalog
├── Historical Knowledge
├── Editorial workflow
└── Discovery queries

Edge capabilities in the same process
├── Media Management
│   ├── binary storage
│   ├── image variants
│   └── streaming provider adapters
└── AI Research (future AI Knowledge Service)
    ├── source ingestion and extraction
    ├── chunking and embeddings
    ├── vector/retrieval index
    ├── RAG answering and evaluation
    └── agent runs and proposals

Entrypoints
├── Web / REST
└── MCP
```

Все блоки находятся в одном codebase и deployment unit. Core вызывает Media и AI application use cases напрямую. Порты используются только между application logic и файловой системой, object storage, image library, AI provider, vector index или streaming provider.

### Сильные кандидаты

1. Единый `Media Service`: MediaAsset bytes и metadata, S3-compatible storage, preview/thumbnail generation, разрешённые source binaries, MediaReference и streaming provider adapters. Он не хранит и не транслирует музыкальное аудио.
2. Единый `AI Knowledge Service`: ingestion, extraction, chunking, embeddings, retrieval/vector index, RAG answering/evaluation и agent runs/proposals. Source и Claims остаются Historical Knowledge.

Средний кандидат — `Discovery/Search Service`, объединяющий внешний text search index, graph/read projections и rebuild. В MVP он остаётся query capability Core; выделение оправдано только независимым масштабированием чтения или специализированным индексом.

MCP и REST являются entrypoints, а не data-owning services. MCP может получить отдельный deployment ради security/network boundary, но продолжает вызывать публичные application/query contracts и не дублирует доменную логику.

People, Music, Dance, Historical Knowledge и Editorial не считаются кандидатами только из-за DDD-границы.

### Рекомендуемая будущая topology

Минимальный целевой вариант:

```text
Core Application ──direct/network contract── Media Service
       │
       └───────────direct/network contract── AI Knowledge Service
```

Discovery остаётся в Core. Это рекомендуемый вариант до доказанной отдельной нагрузки поиска.

Расширенный вариант:

```text
Core Application
├── Media Service
├── AI Knowledge Service
└── Discovery/Search Service
```

Он принимается только при реальной необходимости отдельного search index и projection lifecycle.

Декомпозиция Core на Catalog Service и Historical/Editorial Service не планируется. Она возвращается в обсуждение лишь при независимых командах, release cycles или нагрузке; большое количество доменных связей само по себе является аргументом оставить Core вместе.

## Рассмотренные альтернативы

### Монолит без подготовленных seams

Плюсы: минимум кода сегодня.

Минусы: infrastructure SDK, ORM и транзакции могут проникнуть в application/domain layers; перенос worker потребует переписать core workflow.

### Порты и remote DTO между всеми модулями

Плюсы: внешне напоминает готовность к микросервисам.

Минусы: множество интерфейсов с одной реализацией, дублирование моделей и ложное ощущение, что сетевые semantics уже решены.

### Микросервисы и broker с первого этапа

Плюсы: физическая изоляция сразу.

Минусы: deployment, delivery, retries, observability и data consistency до появления нагрузки и независимых lifecycle.

## Последствия

Положительные:

- infrastructure остаётся заменяемой;
- media и AI jobs можно перенести в worker без переноса доменной модели;
- streaming integrations не превращаются в отдельный малополезный service;
- core monolith сохраняет простые синхронные вызовы;
- границы тестируются без SDK и binary/vector storage.

Отрицательные:

- некоторые ports появятся до второй production implementation, но только на подтверждённых внешних seams;
- выделение service всё равно потребует сетевого контракта, security, retries и observability;
- AIProposal и похожие workflows не могут полагаться на удобную общую транзакцию.
- объединённый Media Service потребует аккуратно различать MediaAsset ownership, playback references и Source rights semantics.

## План изменения

При выделении сначала запускается новый worker из того же codebase и сохраняются application contracts. Затем, если есть независимый lifecycle, вводятся task delivery, idempotency и observability. Отдельный repository/service создаётся последним шагом после ADR о data ownership и migration.

Если кандидат не получает отдельного процесса, порт сохраняется только пока существует реальная внешняя или тестовая заменяемость; бесполезная abstraction удаляется.

## Связанные документы

- [ADR-0001](0001-modular-monolith-context-boundaries.md)
- [ADR-0002](0002-aggregate-and-transaction-boundaries.md)
- [Эволюция инфраструктуры](../roadmap/infrastructure-evolution.md)
- [Media Management](../domain/media-management.md)
