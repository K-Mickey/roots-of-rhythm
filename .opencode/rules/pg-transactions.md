# PostgreSQL transactions

> Транзакционные границы PostgreSQL и SQLAlchemy

- Определять транзакционную границу на уровне use case.
- Использовать UoW как границу write-транзакции; repositories внедрять в operation отдельно при новом и мигрируемом коде по ADR-0008.
- Репозиторий не выполняет неожиданный `commit` и не владеет бизнес-транзакцией.
- Все атомарные изменения выполнять в одной транзакции.
- При ошибке выполнять rollback и не продолжать работу с повреждённой session.
- Внешние сетевые вызовы не удерживают DB-транзакцию без явного обоснования.
- Блокировки, retry и уровень изоляции выбирать по подтверждённому сценарию конкуренции.
- Write-path identity aggregates: `SELECT … FOR UPDATE` с ожиданием (`with_for_update()`, не `NOWAIT`); keyword-only `for_update` на repository `get` / `get_published`, default `False`.
- Discovery, list queries и pre-check unique name — без lock; гонку на INSERT/rename закрывает unique index.
- Межконтекстный write: одна PostgreSQL session и два UoW через явный scope (`music_people_scope`, `knowledge_music_scope`); UoW из `using(session)` не rollback/close на выходе. Это переходный механизм ADR-0006: не использовать pair scopes для read orchestration и не добавлять новый registry-style UoW.
- Cross-context `get_published(..., for_update=True)` вызывать внутри этого scope, до commit.
- Одноконтекстные команды открывают свой UoW на `session_factory`. Discovery — без lock.
- Read use case не открывает UoW без требования transactional snapshot. Параллельные reads используют разные sessions; сначала устранять N+1 и лишние round trips.
