# EPIC-001: исследование жанра

Статус: `accepted`

Tracker: [GitHub issue #1](https://github.com/K-Mickey/roots-of-rhythm/issues/1).

Приоритет поставки: первый epic, подтверждено Product Owner 2026-08-16.

## Пользовательский результат

Visitor изучает Genre как самостоятельную историческую сущность, понимает его характерные признаки, контекст возникновения и место среди других направлений.

## Поддерживаемая ценность

- получить краткий ответ «что это за жанр»;
- увидеть развитие музыки как сеть, а не как строгое дерево;
- понять различия и исторические переходы через объяснённые relations;
- отличить опубликованное утверждение от подтверждённого источниками;
- получить основу для будущей карты, Stories и RAG.

## Объём epic

Включает:

- публичную страницу Genre и её состояния;
- редакционный контент Genre на одном языке проекта;
- все принятые типы Genre relation;
- объяснение, temporal/geographic context, evidence и publication metadata relation;
- controlled seed/import для первого контента;
- последующее расширение страницы связанными сущностями без изменения идентичности Genre.

Не включает:

- полноценные страницы Performer, Group, Песня, Recording и Release — [EPIC-002](../epic-002-performer-group-recording/README.md);
- кликабельный переход на страницу каждого связанного Genre — выполнено в [STORY-002](story-002-navigate-published-genres/README.md);
- карту, поиск, Editorial UI, RAG, MCP и streaming providers;
- Scene и Tradition как обязательные публичные сущности;
- графовую БД или отдельный search index.
- локализацию UI или редакционного контента, locale negotiation, fallback и локализованные URL.

## Stories

1. [STORY-001: открыть опубликованную страницу Genre](story-001-view-published-genre/README.md) — `done`.
2. [STORY-002: перейти между опубликованными Genre](story-002-navigate-published-genres/README.md) — `done`.
3. Показать связанные Performer, Group, Песня, Recording и Release — [STORY-010](../epic-002-performer-group-recording/story-010-genre-related-entities/README.md) ([#36](https://github.com/K-Mickey/roots-of-rhythm/issues/36)) в EPIC-002.
4. Редактировать и публиковать Genre — относится к EPIC-005.

Минимальная главная и identity `/` — [STORY-003](../epic-010-home-search-catalog/story-003-minimal-home/README.md) в EPIC-010, не в этом epic.

Stories 3–4: story 3 формализована в EPIC-002 STORY-010 (`draft`); story 4 остаётся границей планирования (EPIC-005).

Утверждённая техническая декомпозиция STORY-001: [tasks](story-001-view-published-genre/tasks.md) — `accepted`.  
Утверждённая декомпозиция STORY-002: [tasks](story-002-navigate-published-genres/tasks.md) — `accepted`.

## Общие доменные требования

Genre не имеет единственного parent. Historical Knowledge должен уметь выразить пять принятых relation types:

- `influenced`;
- `contributed_to_emergence_of`;
- `developed_from`;
- `overlaps_with`;
- `revival_of`.

Каждая relation является специализированным Claim и содержит subject/target Genre IDs, relation type, объяснение, temporal context, geographic context, editorial status, evidence status, Evidence с ролями `supports | opposes | context` и provenance по общим правилам Claim. `overlaps_with` симметрична и не должна появляться как две независимые истины. `confidence` исключён из Claim MVP.

Поддержка enum не требует искусственно создавать в seed по одному примеру каждого типа. Seed обязан содержать только исторически обоснованные связи.

## Зависимости

- принятый ubiquitous language Genre и Genre relations;
- границы Music Catalog, Historical Knowledge и Discovery;
- согласование минимальных правил публикации;
- согласование [DDD Workshop 005](../../domain/workshops/005-publication-and-visibility.md);
- утверждённый UI contract STORY-001;
- утверждённый data/API workshop и OpenAPI contract STORY-001.

## Отложенные уточнения epic

- точный состав стартовых 6–10 Genre после первого seed;
- момент добавления связанных сущностей.

Переходы между detail pages Genre формализуются в [STORY-002](story-002-navigate-published-genres/README.md).
