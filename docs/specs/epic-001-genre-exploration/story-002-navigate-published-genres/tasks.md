# Декомпозиция STORY-002

Статус: `accepted`.

Story: [STORY-002](README.md).  
Контракты: [UI](ui.md), OpenAPI без изменений (`0.2.0`).

Границы tasks и перенос существующих tests/fixtures утверждены Product Owner 2026-08-19. TASK-001 явно разрешает перемещение существующих test helpers/fixtures без изменения ожиданий.

## Tracker

| Task | GitHub issue |
|---|---|
| `TASK-001` | [#25](https://github.com/K-Mickey/roots-of-rhythm/issues/25) |
| `TASK-002` | [#26](https://github.com/K-Mickey/roots-of-rhythm/issues/26) |
| `TASK-003` | [#27](https://github.com/K-Mickey/roots-of-rhythm/issues/27) |

## TASK-001: вынести повторяющиеся test fixtures

### Результат

Повторяющиеся builders и integration fixtures Genre/Claim/seed живут в одном месте на модуль или в `tests/support`, а тестовые файлы только описывают сценарий.

### Scope

- вынести дубли `_published_genre` / `_claim` из `tests/discovery/application/test_genre_relations.py` и `test_genre_sources.py` в module-local builders или `conftest` discovery;
- вынести общий PostgreSQL `engine` cleanup и вызов `CorpusSeedRunner` из `tests/entrypoints/test_genre_*_integration.py` (и согласовать с `tests/seed/test_corpus_seed.py`, если cleanup совпадает);
- не делать fixtures общим изменяемым доменным состоянием между модулями ([module-structure](../../../module-structure.md));
- не менять проверяемое поведение и не подгонять ожидания;
- не добавлять pytest plugins, factories-фреймворки и новые зависимости.

### Покрывает

Не пользовательский FR. Снижает стоимость STORY-002 и следующих discovery tests.

### Проверка

- те же backend unit и integration команды проходят;
- каждый builder/fixture имеет одного владельца-модуля; копипаста helpers между relations/sources/overview integration удалена.

### Не входит

Новые продуктовые сценарии, frontend test helpers, изменение seed корпуса.

## TASK-002: сделать имена связанных Genre ссылками

### Результат

На публичной Genre page имя связанного опубликованного Genre ведёт на его страницу.

### Scope

- обновить frontend relations UI по [ui.md](ui.md);
- синхронно поправить UI contract STORY-001 формулировку «имя не ссылка» ссылкой на STORY-002;
- обновить Vitest разметки relations;
- не менять API, DTO и domain.

### Покрывает

`FR-001`–`FR-006`, `NFR-001`–`NFR-003`, `AC-1`–`AC-5`.

### Проверка

- component tests: имя — `href` на `/genres/{id}`; тип/explanation не обёрнуты в эту ссылку;
- Playwright: со Swing открываются Jazz и Jump Blues по клику имени.

### Не входит

Главная, identity `/`, list API, slug.

## TASK-003: приёмка навигации Genre

### Результат

Записано evidence AC-1–6 и отсутствие scope creep (каталог/поиск/главная).

### Scope

- прогнать lint/typecheck/unit/integration/e2e, затрагиваемые изменением;
- пройти AC STORY-002;
- актуализировать только документы, которые эта story меняет.

### Покрывает

все AC STORY-002.

## Зависимости

```text
TASK-001 fixtures → TASK-002 links → TASK-003 acceptance
STORY-003 независима
```
