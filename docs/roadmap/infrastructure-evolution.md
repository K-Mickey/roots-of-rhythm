# Эволюция инфраструктуры

Статус: `accepted`

Цель: сохранить ожидаемые направления развития поиска, изображений и RAG, не превращая их в стартовые зависимости. Документ задаёт триггеры обсуждения, а не выбирает облачного поставщика, очередь, vector database или search engine.

## Основной принцип

DDD-граница, процесс и инфраструктурный компонент отвечают на разные вопросы:

- bounded context разделяет предметный язык и владельцев правил;
- aggregate задаёт транзакционную согласованность;
- process/worker изолирует выполнение и масштабирование;
- object storage, index и broker предоставляют технические возможности.

Появление S3-compatible storage или worker не превращает Music Catalog в микросервис. И наоборот, отдельный service не нужен только потому, что данные велики или графоподобны.

Код готовится к выделению не сетевыми abstractions между всеми модулями, а точечными seams:

- внешний или заменяемый механизм находится за портом, принадлежащим использующему application layer;
- порт описывает требуемую возможность, а не SDK или протокол поставщика;
- через границу не передаются ORM objects и открытая DB session;
- сильный кандидат на отдельный процесс не полагается на общую транзакцию с доменным context;
- idempotency key и стабильный ID закладываются только в реально повторяемый workflow;
- внутренние contexts используют явные in-process application contracts, а не имитацию HTTP/RPC.

Port уменьшает связанность с инфраструктурой, но не делает выделение service бесплатным: позднее всё равно появятся network failures, authentication, versioning, retries, observability и другое владение транзакцией.

## Кандидаты на отдельный процесс или service

| Приоритет | Кандидат | Почему граница естественна | Подготовка в монолите | Не делаем сейчас |
|---|---|---|---|---|
| сильный | Единый Media: storage, image processing и streaming adapters | binary I/O, производные файлы, внешние provider failures и общий lifecycle media references | Media Management; storage, image и provider ports | отдельные services для файлов и каждого provider |
| сильный | Единый AI Knowledge: ingestion, embeddings, retrieval, RAG и agents | долгие jobs, внешние модели, перестраиваемый индекс и иной cost/failure profile | AI Research, ports AI/vector providers, идемпотентные jobs/proposals | разделение ingestion/RAG/agents на сервисы |
| средний | Discovery/Search | read-only search/graph projections и независимый rebuild | query DTO; SearchIndex port только при появлении внешнего index | Elasticsearch/OpenSearch и отдельный service без измерений |
| средний | MCP transport | отдельная security и protocol boundary, но нет собственных данных | вызов тех же application/query contracts | дублирование доменных use cases в MCP server |
| слабый | Editorial | тесно координирует lifecycle текущих aggregates | отдельный application workflow и audit contract | собственный service без независимого review domain |
| слабый | People, Music, Dance, Historical Knowledge | много синхронной навигации, общий corpus и нет независимых operational drivers | строгие module/application boundaries и IDs | service на каждый bounded context |

Bounded context является кандидатом на отдельный service только вместе с operational причиной. Соответствие «один context — один service» не принимается.

## Ожидаемые компоненты и триггеры

| Потребность | Начальный вариант | Следующий компонент | Когда он оправдан |
|---|---|---|---|
| Транзакционные и графоподобные данные | одна реляционная БД и таблицы отношений | реплики или отдельное хранилище | измеренная нагрузка или невозможный в текущей модели запрос |
| Поиск по сущностям | возможности реляционной БД, нормализованные поля и простой полнотекстовый поиск | специализированный search engine | измеренно недостаточны релевантность, языковой анализ, facets или latency |
| Semantic retrieval для RAG | небольшой индекс; при PostgreSQL предпочтительно сначала проверить его vector extension | отдельная vector database | индекс требует независимого масштабирования, фильтрации, availability или объёма, которые текущая БД не обеспечивает |
| Изображения и файлы источников | внешние ссылки или локальное development storage | S3-compatible object storage | система начинает принимать или хранить первый управляемый binary asset |
| Доставка изображений | прямой object storage URL через контролируемый adapter | CDN и производные размеры | появились измеримый трафик, latency или стоимость origin delivery |
| Долгие операции | явный ручной или синхронный запуск вне пользовательского запроса | worker из того же codebase | extraction, thumbnails или embeddings выходят за допустимое время запроса и требуют retry |
| Надёжная очередь заданий | DB-backed job state или простой job runner | message broker/task queue | нужна конкуренция workers, backpressure, scheduling или надёжные retries под нагрузкой |
| Рассылка фактов нескольким системам | прямой синхронный вызов | event bus и outbox | появился независимый consumer с требованием гарантированной асинхронной доставки |
| Независимое масштабирование | монолит и при необходимости companion worker | отдельный service | компонент имеет собственные нагрузку, failure isolation и release lifecycle |

## Object storage

S3-compatible object storage вероятно понадобится раньше микросервисов для:

- изображений Performer, Group, Genre, Dance и Story;
- разрешённых копий документов-источников;
- производных thumbnails;
- временных результатов ingestion, если их хранение разрешено.

Media Management владеет MediaAsset metadata и на старте сохраняет их в общей реляционной БД: provenance, rights/license, attribution, alt text, owner references и editorial status. Object storage хранит bytes по непрозрачному key. После выделения Media Service ownership переезжает вместе с этими metadata; публичный URL остаётся представлением, а не identity материала.

Перед внедрением нужно принять отдельное решение о правах доступа, signed URLs, удалении, backup и жизненном цикле оригиналов/производных файлов.

## Vector search и RAG

Отдельная vector database не является обязательным следующим шагом. Для небольшого корпуса выгоднее держать transactional metadata и vector references рядом, если выбранная реляционная БД обеспечивает требуемый поиск.

Переход к отдельной vector database рассматривается, когда измерения показывают одно из следующего:

- retrieval index масштабируется независимо от основного каталога;
- необходимая фильтрация или hybrid search плохо выражается текущим решением;
- rebuild и ingestion мешают транзакционной нагрузке;
- требования latency или availability отличаются от основного приложения;
- эксплуатационная стоимость отдельного компонента ниже стоимости дальнейшей оптимизации текущего.

Vector index остаётся производным от SourceFragment. Его можно перестроить; он не становится источником исторической истины.

## Search engine

Большое число связей не означает автоматическую необходимость Elasticsearch/OpenSearch или графовой БД. Основная карта строится по явным relations и Claims, а стартовый каталог мал.

Специализированный search engine возвращается в обсуждение при реальных требованиях к опечаткам, морфологии нескольких языков, ranking, facets, подсветке и latency. До этого отдельный индекс добавляет синхронизацию, rebuild, monitoring и ещё один источник частичных отказов.

## Worker, task queue и event bus — не одно и то же

| Механизм | Что передаётся | Пример проекта |
|---|---|---|
| Синхронный вызов | команда с немедленным результатом | опубликовать Claim |
| Task queue | задание, которое должен выполнить один worker | построить thumbnails или embeddings |
| Event bus | факт для нуля или нескольких независимых consumers | `ClaimPublished` для search, analytics и notifications |

Для RAG ingestion и изображений первым полезным шагом вероятнее будет worker и task queue, а не event bus. Worker может запускаться из того же репозитория и использовать те же application contracts; это ещё не требует разделения доменных contexts на микросервисы. Streaming provider adapters остаются синхронными или плановыми задачами Media Management и не получают отдельный service.

## Возможная последовательность

### Этап A — стартовый монолит

- приложение и реляционная БД;
- синхронные use cases;
- простой Discovery query layer;
- внешние media references;
- Media Management и image processing внутри монолита на инфраструктурном краю, когда появится первая использующая story;
- без broker, event bus и специализированных indexes.

### Этап B — инфраструктурные adapters

- S3-compatible storage при появлении управляемых файлов;
- vector extension или минимальный индекс при реализации RAG;
- отдельный worker process из того же codebase для долгих ingestion/media jobs;
- DB-backed состояние заданий, если оно достаточно.

### Этап C — специализированные компоненты

- task broker при реальной очереди и нескольких workers;
- search engine или отдельная vector database по результатам измерений;
- CDN при измеренной нагрузке на media;
- outbox/event bus только для конкретных независимых subscribers.

### Этап D — выделение services

Первыми кандидатами являются единый Media Service и единый AI Knowledge Service, поскольку у них отдельные ресурсы и failure model. Discovery/Search является условным третьим кандидатом. Bounded contexts не обязаны становиться сервисами один к одному.

Service выделяется только после фиксации:

- независимого lifecycle и владельца;
- отдельного профиля нагрузки;
- требований failure isolation;
- сетевого контракта;
- ownership данных;
- retries, idempotency, observability и миграционного плана.

## Сейчас не выбираем

- cloud и S3-compatible provider;
- CDN;
- vector database;
- search engine;
- task framework и broker;
- границы будущих services;
- численные thresholds до появления измерений.

Эти non-decisions сохраняют возможность развития, но не входят в стартовый стек.

## Принятое решение

Порядок развития и группировка будущих компонентов приняты пользователем 2026-08-15. Конкретные технологии всё равно принимаются отдельными ADR перед соответствующим этапом.
