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

- добавить characterization tests для существующих projection и visibility rules;
- измерять query count на representative seeded scenarios без жёсткой привязки к случайным служебным запросам;
- записать baseline и целевой budget перед оптимизацией;
- не менять production query plan в этой задаче.

### Проверка

Повторяемый query count, одинаковый DTO до и после instrumentation, отсутствие draft/deleted leakage.

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

### Результат

Пилотные write operations получают repositories отдельно, а UoW определяет только lifecycle одной атомарной PostgreSQL-транзакции.

### Изменения

- определить минимальный transaction scope port без repository properties;
- перевести наиболее нагруженные cross-context write paths, сохранив одну session, `FOR UPDATE`, порядок locks, commit и rollback;
- не создавать новые pair scopes или god UoW;
- действующие registry-style UoW и scopes оставить для ещё не мигрировавших операций;
- не переносить child-session/ContextVar infrastructure из `ncip-api`.

### Проверка

Атомарность при отказе второго context, write locks, rollback, отсутствие лишних repositories в constructor operation.

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

## ARCH-006: wiring и архитектурные guardrails

Tracker: [#63](https://github.com/K-Mickey/roots-of-rhythm/issues/63).

Зависит от `ARCH-002`, `ARCH-004` и `ARCH-005`.

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

Зависит от стабилизации interfaces в `ARCH-002`, `ARCH-004` и `ARCH-005`.

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

## Зависимости и порядок

```text
ARCH-001 baseline ─┬─> ARCH-002 readers ─┐
                   └─> ARCH-003 N+1 ─────┼─> ARCH-006 guardrails ─> ARCH-007 test cleanup
ARCH-004 UoW ─────────> ARCH-005 use cases ┘

ARCH-008 service columns — независимая задача
```

Correctness tests изменяются вместе с каждой production-задачей. В `ARCH-007` откладывается только общий structural cleanup test doubles и дублирования, а не проверка промежуточных рефакторингов.

GitHub issues создаются только после tracker dry run и отдельного подтверждения пользователя.

Решение и порядок задач приняты пользователем 2026-08-30.
