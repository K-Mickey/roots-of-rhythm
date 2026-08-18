# ADR-0005: сервисные колонки persistence и soft-delete

Статус: `proposed`

Дата: 2026-08-18.

## Контекст

Таблицы Music Catalog и Historical Knowledge пока хранят только доменные поля. Нужна единая политика для аудита времени жизни строки и безопасного удаления без немедленного физического `DELETE` identity aggregates. Отдельно нужно не смешивать редакционный `editorial_status=archived` с техническим tombstone и не усложнять owned many-to-many коллекции soft-delete на каждой rewrite-операции.

## Решение

Каждая persistence-таблица проекта содержит сервисные колонки:

| Колонка | Тип | Кто пишет |
|---|---|---|
| `created_at` | `TIMESTAMPTZ NOT NULL` | БД: `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ NOT NULL` | БД: `DEFAULT now()` и trigger `BEFORE UPDATE`, выставляющий `NEW.updated_at = now()` |
| `deleted` | `BOOLEAN NOT NULL DEFAULT false` | Application при soft-delete; обычные repository reads фильтруют `deleted = false` |

Отдельный `deleted_at` не вводится: момент soft-delete отражается в `updated_at` того же `UPDATE`, который ставит `deleted = true`.

Разделение осей:

- `editorial_status=archived` — редакционный вывод из публичного корпуса; возможен republish.
- `deleted=true` — технический tombstone; обычные application queries строку не возвращают.

Поведение удаления:

- Identity aggregates (Genre/`classification_concepts`, Claim, Source, SourceVersion, SourceFragment) — только soft-delete; application не делает hard `DELETE`.
- Owned/link rows без самостоятельной жизненной ценности (сейчас `claim_evidence_references`) — hard `DELETE` при rewrite коллекции допустим; сервисные колонки на таблице всё равно присутствуют для единообразия схемы.
- Test fixtures могут `TRUNCATE`/`DELETE`.

Уникальность identity-сущностей, которые могут быть пересозданы после soft-delete, выражается partial unique index с `WHERE deleted = false` (canonical name Genre; endpoints+type Claim).

Сервисные колонки остаются concern infrastructure/persistence и не обязаны входить в domain msgspec aggregates на первом шаге. Mapping при UPDATE явно копирует только доменные поля и не трогает `created_at` / `updated_at` / `deleted`. Soft-delete identity aggregates выставляет `deleted = true` в repository (для Source/SourceVersion — с soft-cascade на дочерние rows).

Пока не добавляются: `created_by` / `updated_by` (EPIC-005 Editorial audit), optimistic `version`, admin API `include-deleted`.

## Рассмотренные альтернативы

### Только `deleted_at` без boolean

Плюсы: одна колонка, «время удаления» явно.

Минусы: фильтр `IS NULL` менее явный; для «живых» строк нет симметричного boolean; soft-delete всё равно нужен `updated_at` отдельно.

### Soft-delete и для owned evidence references

Плюсы: единое правило на все таблицы.

Минусы: replace evidence раздувает tombstones; уникальность и чтение коллекции усложняются без пользовательской ценности.

### Timestamps только из application/ORM `onupdate`

Плюсы: меньше SQL triggers.

Минусы: сырой SQL и будущие batch-скрипты легко забывают bump `updated_at`; DB trigger остаётся единым source of truth.

## Последствия

Положительные:

- единый контракт схемы для всех таблиц;
- soft-delete identity aggregates без потери истории строки;
- hard rewrite owned links остаётся простым;
- `archived` и `deleted` не конфликтуют семантически.

Отрицательные:

- каждый read-path должен помнить фильтр `deleted = false`;
- partial unique indexes усложняют миграции;
- точное «время удаления» неотделимо от последнего `updated_at`, если после soft-delete строку ещё разменят (MVP не обновляет tombstones).

Риски:

- ORM update, копирующий все колонки записи, может затереть сервисные поля — adapters должны исключать их из domain overwrite;
- забытый фильтр `deleted` в новом query вернёт tombstones.

## Отмена или миграция

Откат: убрать колонки и trigger миграцией вниз; вернуть полные unique constraints. Hard-deleted evidence rows невосстановимы из soft-delete политики.

## Связанные документы

- [ADR-0002](0002-aggregate-and-transaction-boundaries.md) — Claim владеет ClaimEvidenceReference
- [ADR-0004](0004-application-stack.md) — PostgreSQL persistence
- [architecture.md](../architecture.md)
- [module-structure.md](../module-structure.md)
