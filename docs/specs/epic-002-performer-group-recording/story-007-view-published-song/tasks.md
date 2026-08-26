# Декомпозиция STORY-007

Статус: `accepted`.

Story: [STORY-007](README.md).  
Контракты: [UI](ui.md), [Data/API](data-api-workshop.md), [ADR-0007](../../../decisions/0007-musical-work-recording-and-origin-boundaries.md).

Цель — реализовать Work, авторство, производные произведения и версии текста без зависимости от Recording. Tracker TASK issues создаются только после dry run и отдельного подтверждения Product Owner.

## TASK-001: MusicalWork aggregate и persistence

Tracker: [#42](https://github.com/K-Mickey/roots-of-rhythm/issues/42).

### Результат

Music Catalog хранит MusicalWork с canonical title, aliases, description, period, external identities, provenance и editorial lifecycle. Published Work требует title и provenance, но не требует credits, текста, классификации или Recording.

### Scope

- domain model без HTTP/ORM dependencies;
- stable opaque ID, одинаковые titles допустимы;
- SQLAlchemy mapping, Alembic, repository/UoW, soft-delete и write locks по действующим ADR;
- published list/get скрывают draft, archived и deleted.

### Покрывает

`FR-001`, `FR-002`, `FR-008`, `FR-009`, `NFR-002`, AC-1/3/5/6.

### Проверка

Domain и PostgreSQL integration: publish только с title+provenance; published Work без текста/credits; lifecycle visibility; повторные названия.

### Не входит

Credits, relations, lyrics, HTTP и Recording.

## TASK-002: WorkCredit и производные WorkRelation

Tracker: [#43](https://github.com/K-Mickey/roots-of-rhythm/issues/43).

### Результат

Work получает несколько авторских credits и доказательные связи с производными Works без создания отдельной Interpretation.

### Scope

- WorkCredit: PersonId, role, optional credited_as, provenance, editorial status;
- WorkRelation: `translation_of | adaptation_of | arrangement_of | medley_of`, source/target Work, provenance, evidence status, editorial status;
- publish relation требует published source/target;
- неизвестное авторство не создаёт фиктивный Person;
- предотвращение точного дубля и self-relation.

### Покрывает

`FR-005`, `FR-007`, `FR-011`, `NFR-003`, AC-7.

### Проверка

Несколько credits одного Work; направленная relation; reject self/duplicate/unpublished endpoints; смена исполнителя или Genre не создаёт WorkRelation.

### Не входит

Авторские доли, publisher rights, RecordingCredit и автоматическое определение производного Work.

## TASK-003: LyricsVersion, переводы и права

Tracker: [#44](https://github.com/K-Mickey/roots-of-rhythm/issues/44).

### Результат

Work хранит любое число типизированных версий текста; публичный API раскрывает body только по разрешающей политике SourceVersion.

### Scope

- LyricsVersion: WorkId, BCP 47 language tag, optional label, `performable | reading_translation`, creation method, body, SourceVersionId, provenance/editorial lifecycle;
- LyricsVersionCredit и `translation_of | adaptation_of` relation между точными версиями;
- machine translation только `reading_translation` и только после review;
- deterministic public order из Data/API workshop;
- full body только при разрешающей Source rights/access policy, иначе metadata и безопасная причина недоступности.

### Покрывает

`FR-005`, `FR-007`, `FR-010`, `FR-011`, `NFR-003`, AC-6–9.

### Проверка

Несколько языков и вариантов одного языка; invalid BCP 47; запрет machine+performable; hidden draft; отсутствие body при запрещающей policy; translation relation не дублирует текст.

### Не входит

RecordingLyricsUsage, синхронный машинный перевод, полнотекстовый поиск и общий localization framework.

## TASK-004: controlled seed MusicalWork

Tracker: [#45](https://github.com/K-Mickey/roots-of-rhythm/issues/45).

### Результат

Идемпотентный seed содержит шесть published Works: Sixteen Tons, One O'Clock Jump, Ornithology, Sing, Sing, Sing (With a Swing), Shake, Rattle and Roll и West End Blues.

### Scope

- title и provenance для каждого Work;
- подтверждённые WorkCredit/external identity только при наличии seed source; недостающий автор добавляется как published Person через обычный People Catalog seed, а не строкой внутри Work;
- не добавлять copyrighted lyrics body без подтверждённых прав;
- минимум один пример direct Work classification и одна производная relation только при проверенных данных.

### Покрывает

`FR-008`, `FR-009`, AC-1/6/7.

### Проверка

Повторный seed не дублирует Works, credits, relations или texts; все seeded Works доступны published list; отсутствие текста не мешает публикации.

### Не входит

Recording и выдуманные credits/classification ради заполнения UI.

## TASK-005: Song list/detail API и контракт

Tracker: [#46](https://github.com/K-Mickey/roots-of-rhythm/issues/46).

### Результат

OpenAPI получает `GET /api/v1/songs` и `GET /api/v1/songs/{song_id}` согласно Data/API workshop.

### Scope

- Discovery queries и Litestar routes;
- `SongListResponse`, `SongOverviewResponse`, credits, classifications, related Works и rights-aware lyrics views;
- `SONG_NOT_FOUND` / `INTERNAL_ERROR`;
- API changelog и contract check;
- только published related entities.

### Покрывает

`FR-001`, `FR-002`, `FR-005`–`FR-011`, `NFR-002`, AC-1/5–9.

### Проверка

HTTP list/get, empty list, safe 404, no draft leakage, body access policies, deterministic ordering, generated OpenAPI/contract lint.

### Не входит

Recording summaries, genre facets и frontend.

## TASK-006: `/songs`, `/songs/{id}` и выбор текста

Tracker: [#47](https://github.com/K-Mickey/roots-of-rhythm/issues/47).

### Результат

Visitor из header открывает SSR-каталог и страницу Work, переключает опубликованные версии текста без полной перезагрузки.

### Scope

- routes и header «Песни»;
- optional sections из UI contract;
- accessible `text` selector и browser history;
- unavailable body и machine labels;
- PageError vs not-found;
- `/` без song detail links.

### Покрывает

`FR-001`–`FR-007`, `FR-010`, `NFR-001`, `NFR-004`, AC-1–9.

### Проверка

SSR HTML, keyboard selection, query restore, invalid text fallback, empty sections, header and home boundaries, API failure state.

### Не входит

Recording, genre facets, player и global localization.

## TASK-007: приёмка STORY-007

Tracker: [#48](https://github.com/K-Mickey/roots-of-rhythm/issues/48).

### Результат

Acceptance document связывает AC с воспроизводимыми командами и фактическими результатами; specification, OpenAPI и реализация согласованы.

### Scope

- domain/API/frontend checks всех AC;
- contract lint, backend suite, frontend unit/SSR и минимальный browser flow;
- проверка seed idempotency, секретов и diff;
- обновление статуса только после успешных required checks.

### Покрывает

Все FR/NFR и AC STORY-007.

### Проверка

Команды из `docs/development.md`; непройденные или недоступные проверки перечислены явно.

### Не входит

Исправление unrelated failures и требования STORY-008.

## Зависимости

```text
TASK-001 Work ─┬─> TASK-002 credits/relations ─┐
               └─> TASK-003 lyrics/rights ─────┼─> TASK-004 seed
                                                └─> TASK-005 API → TASK-006 UI → TASK-007 acceptance
```

## Breaking changes и подтверждения

- OpenAPI изменяется аддитивно; версия и changelog фиксируются в TASK-005.
- Alembic migrations создаются в TASK-001/003.
- Тесты изменяются только после отдельного явного подтверждения согласно правилам проекта.
- GitHub issues, branch, commit и PR не создаются без отдельных команд.

## Не создаём отдельные задачи

- Interpretation, Session/Take/Master;
- Elasticsearch, очередь, graph DB и translation service;
- Recording или плеер.
