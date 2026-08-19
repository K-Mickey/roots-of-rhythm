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

- полноценные страницы Performer, Group и Recording;
- кликабельный переход на страницу каждого связанного Genre до реализации соответствующего маршрута;
- карту, поиск, Editorial UI, RAG, MCP и streaming providers;
- Scene и Tradition как обязательные публичные сущности;
- графовую БД или отдельный search index.
- локализацию UI или редакционного контента, locale negotiation, fallback и локализованные URL.

## Stories

1. [STORY-001: открыть опубликованную страницу Genre](story-001-view-published-genre/README.md) — `done`.
2. Добавить навигацию между опубликованными Genre — draft-кандидат после появления нескольких detail pages.
3. Показать связанные Performer, Group и Recording — относится к интеграции с EPIC-002.
4. Редактировать и публиковать Genre — относится к EPIC-005.

Stories 2–4 являются границами планирования, а не утверждённой декомпозицией.

Утверждённая техническая декомпозиция STORY-001: [tasks](story-001-view-published-genre/tasks.md) — `accepted`.

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
- момент добавления связанных сущностей и переходов между detail pages.

Они не блокируют STORY-001 и уточняются соответствующими последующими stories.
