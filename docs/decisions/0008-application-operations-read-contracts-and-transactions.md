# ADR-0008: application operations, read contracts and transaction boundaries

Статус: `accepted`

Дата: 2026-08-30.

## Контекст

Application-слой вырос из небольших lifecycle-сервисов одного aggregate. Эти сервисы остаются связными, пока их методы используют одинаковые repositories и одну транзакционную политику. Одновременно появились составные read operations и межконтекстные write-сценарии. Они выявили другие требования:

- сложные чтения собирают результат из нескольких repositories или bounded contexts и управляют множеством мелких вызовов;
- Unit of Work одновременно служит границей транзакции, владельцем SQLAlchemy session и registry всех repositories контекста;
- новый repository расширяет production и fake UoW, даже если отдельной операции он не нужен;
- pair scopes (`music_people_scope`, `knowledge_music_scope` и аналогичные) сохраняют атомарность межконтекстной записи, но их число растёт вместе с комбинациями контекстов;
- один `AsyncSession` нельзя безопасно использовать конкурентно из нескольких asyncio tasks, поэтому параллелизация чтения требует отдельных sessions, а не только другого application API;
- подробные in-memory fakes всё хуже воспроизводят soft-delete, constraints, locking, rollback и сортировку PostgreSQL.

ADR-0002 определяет aggregate и transaction boundaries, ADR-0006 — пессимистические write locks и текущие pair scopes. Настоящее решение уточняет форму application operations и направление их постепенной миграции, не меняя доменное владение данными.

## Решение

### Application operations

Aggregate отвечает за собственные инварианты и изменение состояния.

Связный application service может обслуживать lifecycle одного aggregate, если его методы имеют близкие зависимости, права и транзакционную политику. Стабильные сервисы не разделяются механически ради правила «один класс — один метод».

Отдельный command use case вводится, когда операция имеет самостоятельный внешний сценарий либо заметно отличается зависимостями, правами, транзакцией или сложностью. Use case получает только необходимые ему ports.

Application service не является обязательным промежуточным слоем. Переиспользуемое правило координации выносится в service или функцию только при реальном повторном использовании либо когда это делает основной сценарий существенно понятнее.

### Read operations и contracts

Простое чтение может использовать обычный repository. Составное чтение оформляется как query use case, когда имеет самостоятельный внешний сценарий, объединяет несколько источников или требует отдельной оптимизации. Наличие query use case не требует обязательного reader и projector.

Bounded context может предоставить предметный public reader, который:

- читает только данные своего контекста;
- возвращает application-owned read DTO, а не ORM models и не изменяемые aggregates;
- применяет принадлежащие контексту правила `published`, `deleted` и access;
- укрупняет batch-загрузки и скрывает persistence plan от вызывающего application layer.

Reader определяется реальным пользовательским чтением (`get_song_data`, `get_recording_data`, `list_recordings`), а не универсальным `get_everything`. Межмодульная operation не выполняет прямой SQL по ORM-моделям нескольких контекстов.

Сборка конечного DTO может быть вынесена в чистую mapper/projector функцию без I/O. Отдельный класс для projector не требуется.

### Unit of Work и sessions

Целевая ответственность Unit of Work — граница атомарной write-транзакции. Repositories внедряются в operation отдельно; добавление repository не должно расширять интерфейс UoW.

Read use case не использует UoW без требования согласованного transactional snapshot. Независимые context readers могут выполняться параллельно, только если каждый владеет отдельной session. Сначала устраняются N+1 и лишние round trips; автоматические child sessions, отдельный read pool и другая сложная concurrency infrastructure вводятся только после измерения latency и нагрузки.

Текущие pair scopes из ADR-0006 остаются переходным механизмом для атомарных cross-context writes. Они не размножаются для read orchestration. Миграция к transaction-only UoW выполняется инкрементально в затрагиваемых write-сценариях с сохранением `FOR UPDATE`, порядка блокировок и одной PostgreSQL-транзакции.

### Validation

Валидация выполняется как можно раньше в правильной границе:

- transport проверяет wire shape и transport-specific ограничения;
- use case проверяет права, доступность зависимостей и правила пользовательского сценария;
- aggregate проверяет собственные инварианты;
- PostgreSQL constraints обеспечивают ссылочную и конкурентную целостность.

Проверки не дублируются в позднем слое только ради удобства вызывающего кода.

## Рассмотренные альтернативы

### Сохранить UoW как registry всех repositories

Плюсы: текущий код и pair scopes не требуют миграции; одна точка доступа к контексту.

Минусы: зависимости operation неявны; UoW и его fakes растут с каждым repository; read orchestration связан с write transaction abstraction; возникают новые комбинированные scopes.

Не выбрано как целевая модель. Сохраняется временно для существующего кода.

### Создать отдельный use case для каждого метода каждого service

Плюсы: малые классы и точные constructor dependencies.

Минусы: механическое дробление связных lifecycle-операций, дополнительные wiring и файлы без изменения ответственности.

Не выбрано. Разделение применяется только при содержательном расхождении операций.

### Разрешить operation прямой межконтекстный SQL

Плюсы: минимальное число запросов и свобода оптимизации одной страницы.

Минусы: вызывающий модуль зависит от чужих ORM-моделей и схемы хранения, обходит application contracts и размывает владение данными.

Не выбрано. Оптимизированный SQL остаётся внутри infrastructure source context за его public reader.

### Ввести универсальные projections, read database или materialized CQRS

Плюсы: независимая оптимизация и масштабирование чтения.

Минусы: синхронизация, rebuild, delivery semantics и эксплуатационная сложность без измеренной необходимости.

Не выбрано. Производные projections остаются возможной будущей реализацией существующих read contracts.

## Последствия

Положительные:

- application operations получают явные и узкие зависимости;
- составные query use cases управляют несколькими предметными результатами вместо деталей repositories;
- source contexts сохраняют владение данными и локальную оптимизацию SQL;
- UoW перестаёт расти вместе с количеством repositories;
- unit-тесты могут использовать малые stubs/readers, а persistence semantics остаётся в PostgreSQL integration tests;
- архитектура допускает дальнейшую оптимизацию чтения без изменения публичного API.

Отрицательные:

- во время миграции одновременно существуют registry-style и transaction-only UoW;
- появляются отдельные read DTO и mapping между context reader и вызывающим query use case;
- неправильная гранулярность reader может заменить множество repository methods множеством почти одинаковых query methods;
- параллельное чтение увеличивает использование connection pool и не видит незакоммиченные изменения другой session.

Риски и ограничения:

- public reader не должен превратиться в универсальный фасад всего контекста;
- межконтекстные правила видимости нельзя незаметно перенести к одному source context;
- query count и latency измеряются до добавления concurrency infrastructure;
- DI framework, event bus, отдельная read database и materialized projections этим решением не вводятся.

## Миграция и отмена

Миграция выполняется небольшими вертикальными шагами:

1. зафиксировать поведение и query count выбранной тяжёлой read operation;
2. проверить context reader и чистый projector на одном составном query use case;
3. устранить подтверждённые N+1 и добавить предметные batch reads;
4. отделить repositories от UoW в наиболее нагруженных cross-context write operations;
5. выделять command use cases только из сервисов с расходящимися зависимостями или транзакциями;
6. после стабилизации interfaces упростить fakes и повторяющиеся test builders.

Каждый шаг обратим независимо: operation может временно вернуться к прежнему port, не меняя domain model, database schema или публичный API. Если context readers не уменьшают сложность и query count, текущие repository contracts сохраняются, а дальнейшее распространение подхода прекращается.

Связанные решения: [ADR-0001](0001-modular-monolith-context-boundaries.md), [ADR-0002](0002-aggregate-and-transaction-boundaries.md), [ADR-0003](0003-extraction-ready-monolith.md), [ADR-0006](0006-pessimistic-write-locks.md), [DDD Workshop 003](../domain/workshops/003-context-map.md), [DDD Workshop 004](../domain/workshops/004-aggregate-boundaries.md).

Решение принято пользователем 2026-08-30.
