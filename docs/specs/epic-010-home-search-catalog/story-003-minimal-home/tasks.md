# Декомпозиция STORY-003

Статус: `accepted`.

Story: [STORY-003](README.md).  
Контракты: [UI](ui.md), [Data/API](data-api-workshop.md).  
OpenAPI без изменений.

Границы tasks утверждены Product Owner 2026-08-19 вместе со story (главная без жанров).

## Tracker

| Task | GitHub issue |
|---|---|
| `TASK-001` | [#28](https://github.com/K-Mickey/roots-of-rhythm/issues/28) |
| `TASK-002` | [#29](https://github.com/K-Mickey/roots-of-rhythm/issues/29) |

## TASK-001: сверстать центрированную главную и снять stub identity

### Результат

`/` показывает крупное имя продукта и короткое описание по центру; identity и not-found ведут на `/`.

### Scope

- реализовать `app/page.tsx` (или эквивалент) по [ui.md](ui.md);
- header identity `href="/"`;
- not-found Genre: ссылка на `/`;
- Vitest: title + description, нет Genre links, identity `/`;
- Playwright: открыть `/`, проверить заголовок и описание, identity, not-found → `/`.

### Покрывает

`FR-001`–`FR-005`, `NFR-001`–`NFR-003`, `AC-1`–`AC-6`.

### Не входит

List API, каталог жанров, статистика, primary nav, карта.

## TASK-002: приёмка HOME-0

### Результат

Evidence AC-1–6; на `/` нет жанров и дашборда.

### Scope

- прогнать frontend lint/typecheck/unit/e2e, затрагиваемые изменением;
- пройти AC STORY-003;
- актуализировать `docs/development.md`, если появился канонический URL `/`.

### Покрывает

все AC STORY-003.

## Зависимости

```text
TASK-001 home UI → TASK-002 acceptance
STORY-002 независима
```
