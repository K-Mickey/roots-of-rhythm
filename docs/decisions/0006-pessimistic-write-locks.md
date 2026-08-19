# ADR-0006: пессимистические lock на write-path

Статус: `proposed`

Дата: 2026-08-20.

## Контекст

Identity aggregates (Person, Genre, ClassificationAssignment, Claim, Source, SourceVersion, SourceFragment) изменяются короткими write-командами в одной PostgreSQL-транзакции. Без явной блокировки параллельные `replace_content` и status transitions приводят к lost update: последний `UPDATE` перезаписывает поля без ошибки.

Workshop 004 и ADR-0005 откладывали optimistic `version`. Конкурентных редакторов между bounded contexts пока нет: write-path — seed, внутренние команды и integration tests.

Публикация assignment и claim читает строки другого контекста (Person / Genre) в той же транзакции, иначе проверка published и mutate расходятся (TOCTOU).

## Решение

На write-path identity-агрегатов использовать `SELECT … FOR UPDATE` (ожидание, без `NOWAIT` / `SKIP LOCKED`) **в той же транзакции, что и mutate**:

- первый load корня перед mutate — `for_update=True`;
- повторный SELECT в `save` / `mark_deleted` — тоже `for_update=True`;
- родитель при insert дочерней строки в том же контексте (`create_version` → Source, `create_fragment` → SourceVersion);
- soft-delete каскад Source: lock родителя, затем UPDATE детей;
- ссылки того же Unit of Work: Genre при publish assignment (id по возрастанию); SourceFragment при replace_evidence / publish claim (id по возрастанию).

Discovery, публичные read queries и pre-check `canonical_name_exists` **не** блокируют строки. Гонку на INSERT/rename закрывают partial unique indexes и `UniqueConstraintViolation`.

API репозиториев: keyword-only `for_update: bool = False` на `get` / `get_published` / parent loads. Infrastructure применяет `statement.with_for_update()` через `apply_write_lock`.

Межконтекстный write (publish assignment / claim, create claim draft) идёт через явный command scope: одна PostgreSQL session, два UoW без владения session (`UnitOfWork.using(session)`). Scope живёт в корневом `infrastructure` (`music_people_scope`, `knowledge_music_scope`). Application-сервис принимает factory этого scope, не `session_factory` и не SQLAlchemy.

Одноконтекстные команды (Genre, Person, Source) остаются на `lambda: SqlAlchemy*UnitOfWork(session_factory)`.

Optimistic `version` не вводится.

## Рассмотренные альтернативы

### Shared `session_factory` на application-сервисе и dual-publish

Плюсы: одна транзакция на publish.

Минусы: SQLAlchemy в application, дублирование publish-путей, UoW с factory XOR session.

### Вложенный UoW через contextvar / присоединение к текущей session

Плюсы: lookup другого контекста выглядит как отдельный UoW.

Минусы: неявный lifecycle session (inner не rollback/close); трудно рассуждать о commit.

Не выбрано: явный scope на пару UoW.

### Optimistic locking (`version` / ETag)

Плюсы: читатели не блокируются; явный конфликт при stale write.

Минусы: миграция схемы и политика retry в API; избыточно для коротких внутренних команд.

### `FOR UPDATE NOWAIT`

Плюсы: быстрый fail при конкуренции.

Минусы: второй писатель не дожидается commit первого.

## Последствия

Положительные:

- lost update на корне write-команды закрыт;
- publish assignment/claim держит Person/Genre до commit одной транзакции;
- application-сервисы не знают про SQLAlchemy session;
- межконтекстная транзакция видна в constructor (scope factory), а не в скрытом contextvar.

Отрицательные:

- параллельные писатели одной строки выстраиваются в очередь;
- `ClaimService` / `ClassificationAssignmentService` открывают оба UoW даже на read-методах той же фабрики;
- `using()`-UoW не закрывает session — это обязанность scope.

Риски:

- забытый `for_update` на cross-context load внутри publish снова открывает TOCTOU;
- новый межконтекстный use case без scope снова получит две транзакции.

## Отмена или миграция

Optimistic `version` — отдельный ADR. Выделение контекстов в разные БД потребует идемпотентных шагов вместо shared session.
