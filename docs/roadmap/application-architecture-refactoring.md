# Рефакторинг application architecture

Статус: `accepted`.

Дата: 2026-08-30.

Основание: [ADR-0008](../decisions/0008-application-operations-read-contracts-and-transactions.md).

Цель — инкрементально упростить тяжёлые read/write operations, отделить транзакцию от registry repositories и сократить расхождение test fakes с PostgreSQL. Публичное поведение, domain model и API не меняются без отдельной продуктовой задачи.

## ARCH-001: baseline составных read operations

Tracker: [#58](https://github.com/K-Mickey/roots-of-rhythm/issues/58).

### Результат

Для `SongOverviewQuery` и `RecordingOverviewQuery` зафиксированы текущее публичное поведение, число SQL-запросов и наиболее дорогие последовательности загрузки.

### Изменения

- измерять query count только для HTTP-запроса внутри запущенного `TestClient`, исключая seed и setup;
- сохранить существующие DTO и visibility assertions без отдельных дублирующих characterization tests;
- записать baseline и ceilings перед оптимизацией:

| Operation | Music | People | Historical/rights | Ceiling |
| --- | ---: | ---: | ---: | ---: |
| Song overview (`Sixteen Tons`) | 13 | 1 | 4 | 18 |
| Recording overview (`Tennessee Ernie Ford`) | 10 | 1 | 5 | 16 |

- не менять production query plan в этой задаче.

### Проверка

Повторяемый query count, одинаковый DTO до и после instrumentation, отсутствие draft/deleted leakage. `ARCH-002` и `ARCH-003` не превышают эти ceilings и могут снизить их только после измеренного рефакторинга.

## ARCH-002: пилот context public readers

Tracker: [#59](https://github.com/K-Mickey/roots-of-rhythm/issues/59).

Зависит от `ARCH-001`.

### Результат

`SongOverviewQuery` управляет несколькими предметными read results, а не набором repositories Music/People/Historical Knowledge. По результату пилота принимается решение о переносе `RecordingOverviewQuery` тем же способом.

### Изменения

- определить минимальные application-owned read DTO и public reader ports у контекстов-владельцев;
- Music reader пакетно загружает нужные Work, Recording, Lyrics и Genre данные только из Music Catalog;
- People и Historical Knowledge readers применяют собственные published/deleted rules;
- Discovery сохраняет межконтекстную visibility и собирает конечный DTO;
- прямые импорты чужих ORM-моделей, универсальный `get_everything` и отдельная read database не добавляются;
- чистый projector выделяется функцией только там, где отделяет I/O от сборки DTO.

### Проверка

Публичный результат совпадает с baseline; число запросов не растёт; source-context boundaries не нарушены.

## ARCH-003: устранение подтверждённых N+1 и лишних round trips

Tracker: [#60](https://github.com/K-Mickey/roots-of-rhythm/issues/60).

Зависит от `ARCH-001`; выполняется после или вместе с результатами `ARCH-002`.

### Результат

Из тяжёлых overview/list operations устранены фактические загрузки по одному ID и повторные запросы одинаковых данных.

### Изменения

- составить inventory циклов `get` и повторных reads по query-count evidence;
- при известном наборе ID добавлять предметный batch method либо укрупнять запрос внутри context reader;
- пустой batch не выполняет SQL, отсутствующие IDs не создают placeholder, порядок восстанавливает application layer при необходимости;
- не добавлять `get_many` во все repositories ради симметрии;
- параллельные sessions вводить только если batching не укладывается в утверждённый budget.

### Проверка

Query budgets `ARCH-001`, пустые и частичные batches, детерминированный порядок, прежняя публичная видимость.

## ARCH-004: transaction-only Unit of Work

Tracker: [#61](https://github.com/K-Mickey/roots-of-rhythm/issues/61).

Статус: `implemented` (пилот `RecordingService`, 2026-08-31).

### Результат

Пилотные write operations получают repositories отдельно, а UoW определяет только lifecycle одной атомарной PostgreSQL-транзакции.

### Изменения

- определить минимальный transaction scope port без repository properties;
- перевести наиболее нагруженные cross-context write paths, сохранив одну session, `FOR UPDATE`, порядок locks, commit и rollback;
- не создавать новые pair scopes или god UoW;
- действующие registry-style UoW и scopes оставить для ещё не мигрировавших операций;
- не переносить child-session/ContextVar infrastructure из `ncip-api`.

Пилот выполнен для всего lifecycle `RecordingService`: transaction scope создаёт одну SQLAlchemy session на operation, а repositories создаются явно только для нужной operation и привязываются к этой session. `music_people_scope` и registry-style UoW остаются для остальных services.

В мигрированном write-path repository выполняет `flush` и переводит только принадлежащие ему unique constraints во внутреннюю application-ошибку; transaction scope отвечает за общий rollback. Остальные repositories проверяются по мере переноса их services/use cases.

### Проверка

Атомарность при отказе второго context, write locks и rollback.

## ARCH-005: пилот command use cases

Tracker: [#62](https://github.com/K-Mickey/roots-of-rhythm/issues/62).

Зависит от `ARCH-004`.

### Результат

Самостоятельные сложные операции отделены от связных lifecycle services по критериям ADR-0008, без массового правила «один метод — один класс».

### Изменения

- первым пилотом выделить publish и published replace-content paths из `RecordingService`, поскольку они используют Work и People dependencies, которых не требуют create/archive;
- сохранить малые Genre, Person, Group, MusicalWork и аналогичные lifecycle services;
- после пилота отдельно оценить `ClaimService`, `RecordingOriginClaimService` и `ClassificationAssignmentService`; не включать их механически в эту задачу;
- HTTP/CLI вызывают application operation и не получают domain/persistence orchestration.

### Проверка

Прежние ошибки и транзакции Recording, узкие constructor dependencies, отсутствие дополнительного промежуточного service без самостоятельного правила.

## ARCH-005B: rollout command use cases

Tracker: `TBD` до следующей синхронизации tracker.

Зависит от `ARCH-005`.

### Результат

Подход, проверенный на `RecordingService`, применяется к оставшимся сложным lifecycle services. Вместе `ARCH-005` и `ARCH-005B` охватывают пять объектов: `Recording`, `ClassificationAssignment`, `GenreRelationClaim`, `RecordingOriginClaim` и `ListeningGuide`.

### Изменения

- выделить `PublishClassificationAssignment` из `ClassificationAssignmentService`; create, replace и archive оставить связным lifecycle service;
- выделить create-draft и publish operations из `ClaimService` для aggregate `GenreRelationClaim`; редактирование content/evidence и archive оставить сервису;
- выделить create-draft и publish operations из `RecordingOriginClaimService`; редактирование content/evidence и archive оставить сервису;
- выделить `PublishListeningGuide` из `ListeningGuideService`; create, replace observations и archive оставить сервису, при этом изменение уже published guide сохраняет повторную проверку Recording;
- каждому use case передавать только необходимые repositories и transaction boundary; не создавать общий command facade или класс на каждый простой lifecycle method;
- сохранить одну PostgreSQL-транзакцию для cross-context writes, существующий порядок `FOR UPDATE`, атомарный rollback и прежние application errors;
- после переноса удалить более не используемые pair scopes и registry-style UoW dependencies только при отсутствии callers.

`WorkRelationService`, `LyricsVersionRelationService` и `SourceService.set_access_policy` в эту задачу не входят: их зависимости пока недостаточно отличаются для обязательного выделения use case.

### Проверка

Прежнее поведение create/edit/publish/archive, узкие constructor dependencies, атомарность при ошибке второго context, write locks, rollback и отсутствие новых pair/god UoW.

## ARCH-006: wiring и архитектурные guardrails

Tracker: [#63](https://github.com/K-Mickey/roots-of-rhythm/issues/63).

Зависит от `ARCH-002`, `ARCH-004` и `ARCH-005B`.

### Результат

Dependency assembly отражает новые contracts, а автоматические проверки не позволяют вернуть межконтекстные ORM imports и registry-style UoW в мигрированный код.

### Изменения

- обновить ручной dependency wiring без нового DI framework;
- добавить architecture checks для направления imports и ownership public readers;
- запретить Discovery/application operations импортировать infrastructure другого context;
- удалить переходные factories только когда у них не осталось callers;
- синхронизировать architecture/module documentation с фактическим состоянием миграции.

### Проверка

Architecture tests, typecheck, полный поиск callers удаляемых contracts и обычный project quality gate.

## ARCH-007: упрощение test doubles и повторяющихся setup

Tracker: [#64](https://github.com/K-Mickey/roots-of-rhythm/issues/64).

Зависит от стабилизации interfaces в `ARCH-002`, `ARCH-004` и `ARCH-005B`.

### Результат

Unit-тесты используют малые stubs/fakes нужных ports, а PostgreSQL integration tests проверяют persistence semantics. Перегруженный `music_catalog/fakes.py` больше не является registry всего context.

### Изменения

- разделить fake repositories/readers по предметным группам только для реальных потребителей;
- заменить fake UoW на transaction stub и явно переданные fake repositories в мигрированных operations;
- вынести module-local builders только для повторяющихся сложных Recording, LyricsVersion и Claim scenarios;
- простые значения оставлять в тесте;
- удалить дублирующие тесты лишь после сопоставления проверяемого поведения;
- не создавать универсальный generic fake repository или новый test framework.

### Проверка

Одинаковое покрытие domain/application сценариев, repository semantics в PostgreSQL integration tests, отсутствие неиспользуемых fixtures и заметное уменьшение общего fake setup.

## ARCH-008: аудит service columns и soft-delete schema

Tracker: [#65](https://github.com/K-Mickey/roots-of-rhythm/issues/65).

Задача независима от `ARCH-001`–`ARCH-007` и может выполняться раньше.

### Результат

Все persistence-таблицы соответствуют единому контракту [ADR-0005](../decisions/0005-persistence-service-columns-and-soft-delete.md), а расхождения исправлены одной следующей Alembic migration.

### Изменения

- сопоставить SQLAlchemy metadata, всю migration history и фактическую PostgreSQL schema;
- для каждой таблицы проверить `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` и `deleted BOOLEAN NOT NULL DEFAULT false`;
- проверить `BEFORE UPDATE` trigger `set_updated_at`, обычные read-фильтры `deleted = false`, soft-delete identity roots и разрешённую политику owned/link rows;
- проверить partial unique indexes, которые должны игнорировать tombstones;
- добавить только недостающие columns, defaults, triggers, indexes и repository filters; существующие данные backfill выполнить безопасно в migration;
- добавить schema-level integration check, чтобы новые таблицы не обходили контракт;
- отдельно вынести ADR-0005 на review статуса после фактического аудита.

### Не входит

`created_by`, `updated_by`, `deleted_at`, optimistic `version`, admin restore API и изменение editorial lifecycle.

### Проверка

Upgrade с текущей schema, downgrade новой migration, повторный metadata/schema audit, timestamp bump после UPDATE, soft-delete visibility и partial uniqueness.

## ARCH-009: финальная организация application packages

Tracker: `TBD` до следующей синхронизации tracker.

Зависит от `ARCH-006`, `ARCH-007` и завершения `ARCH-008`. Выполняется последней перед итоговой приёмкой архитектурного рефакторинга.

### Результат

Оставшиеся application-файлы разложены по устойчивым предметным каталогам после стабилизации readers, use cases и transaction contracts. Навигация отражает ответственность кода, а не историю его появления.

### Изменения

- завершить перенос Discovery operations в `queries/`, чистых сборщиков DTO в `projections/`, DTO и errors — в предметные модули соответствующих packages;
- в каждом bounded context собрать связные lifecycle services в `application/services/`, а самостоятельные command operations из `ARCH-005/005B` — в `application/use_cases/`;
- ports, public read contracts и infrastructure adapters оставить в их собственных существующих границах, не смешивать их с services/use cases;
- обновить imports, package exports, dependency wiring, tests и architecture documentation без compatibility-фасадов и массовых re-export;
- удалить пустые и устаревшие модули только после проверки всех callers;
- не объединять несвязанные services в один файл и не создавать базовые классы, registry или новый framework ради структуры каталогов.

### Проверка

Полный поиск старых import paths и callers, architecture checks, отсутствие циклических imports, неизменные public contracts/query budgets и полный project quality gate.

## Зависимости и порядок

```text
ARCH-001 baseline ─┬─> ARCH-002 readers ─┐
                   └─> ARCH-003 N+1 ─────┼─> ARCH-006 guardrails ─> ARCH-007 test cleanup
ARCH-004 UoW ─────────> ARCH-005 pilot ─> ARCH-005B rollout ┘

ARCH-008 service columns ─────────────────────────────────────────┐
ARCH-006 + ARCH-007 ────────────────────────────────> ARCH-009 package layout ─> acceptance
```

Correctness tests изменяются вместе с каждой production-задачей. В `ARCH-007` откладывается только общий structural cleanup test doubles и дублирования, а не проверка промежуточных рефакторингов.

GitHub issues создаются только после tracker dry run и отдельного подтверждения пользователя.

Решение и порядок задач приняты пользователем 2026-08-30.
