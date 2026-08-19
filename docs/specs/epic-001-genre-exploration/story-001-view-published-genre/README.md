# STORY-001: открыть опубликованную страницу Genre

Статус: `accepted`

Tracker: [GitHub issue #22](https://github.com/K-Mickey/roots-of-rhythm/issues/22).

Epic: [EPIC-001](../README.md).

## User story

Как Visitor, я хочу открыть опубликованную страницу Genre Swing, чтобы получить краткое определение жанра, увидеть его исторический контекст и понять объяснённые связи с другими Genre.

## Проблема и измеримый результат

Пользователю сейчас приходится собирать определение и историю переходов из разрозненных источников. Story успешна, если Visitor без авторизации открывает страницу Swing, видит доступное содержание и relations, понимает подтверждённость утверждений, а отсутствие необязательных данных не ломает страницу и не создаёт ложных фактов.

## Контекст

Это первый вертикальный срез через сохранение данных, доменные правила, public query, API и frontend. Данные загружаются контролируемым seed/import; Editorial UI появится позже.

## Functional requirements

- `FR-001` Visitor может без авторизации открыть опубликованный Genre по стабильной публичной identity.
- `FR-002` Страница поддерживает секции: header, definition, period, geography/origin context, characteristic features, formation process, Genre relations, musical examples, Performer/Group, dances, Stories, sources и primary image.
- `FR-003` Для опубликованного Genre обязательны `name` и краткое `definition`. Остальные секции и поля опциональны.
- `FR-004` Отсутствующие опциональные секции не показываются Visitor и не заменяются сохранённым фиктивным значением.
- `FR-005` Страница показывает только опубликованные Genre и опубликованные Claims/relations; draft-данные Visitor недоступны.
- `FR-006` Relation показывает название связанного Genre, тип связи, explanation, temporal context, geographic context и evidence status; неполный draft допустим, но никогда не попадает в публичный ответ.
- `FR-007` Relation показывает `unverified`, `supported` или `disputed` и доступные прошедшие review Evidence/Source references. `supported` требует поддерживающее Evidence, а `disputed` — противоречащий материал и объяснение разногласия.
- `FR-008` Модель поддерживает `influenced`, `contributed_to_emergence_of`, `developed_from`, `overlaps_with` и `revival_of` со значениями и направлениями, определёнными DDD Workshop 001.
- `FR-009` `overlaps_with` отображается как симметричная связь независимо от того, с какой стороны открыта страница, без дублирования одной истины.
- `FR-010` До появления detail route связанного Genre его название не превращается в неработающую ссылку.
- `FR-011` Seed содержит Genre Swing, Jazz и Jump Blues, а также два поддержанных Evidence Claims: `Swing developed_from Jazz` и `Swing contributed_to_emergence_of Jump Blues`. Наличие примера каждого relation type в seed не требуется.
- `FR-012` Первая story не требует создания Performer, Group, Recording или их страниц.
- `FR-015` Draft GenreRelation требует только subject Genre, target Genre и relation type; остальные поля можно заполнить позднее. Публикация разрешена только после выполнения всех обязательных и условных правил DDD Workshop 005.
- `FR-016` Public API разделяет Genre page на overview, relations и sources projections; каждая загружается отдельно, а public visibility Genre одинакова для всех трёх operations.

## Non-functional requirements

- `NFR-002` Страница остаётся доступной и содержательно понятной без JavaScript-интерактивности карты, авторизации, изображений и внешних media providers.
- `NFR-003` Структура не предполагает единственного parent Genre и допускает несколько входящих, исходящих и симметричных relations.
- `NFR-004` Overview, relations и sources read models не становятся источником истины для Genre, Claim или Source и могут быть перестроены.
- `NFR-005` Реализация не требует графовой БД, Elasticsearch, очереди или отдельного сервиса.
- `NFR-006` Empty states и evidence status доступны не только через цвет или изображение.

## Acceptance criteria

1. Given опубликованный Swing, when Visitor открывает страницу, then он видит название, определение и все заполненные секции.
2. Given у Swing не заполнены любые опциональные поля или коллекции, when Visitor открывает страницу, then соответствующие секции скрыты, а страница не показывает `null`, пустой заголовок, сломанную карточку или выдуманное значение.
3. Given у Swing есть опубликованная Genre relation, when Visitor просматривает её, then видит связанный Genre, точный тип, объяснение, доступный период/географию и evidence status.
4. Given relation имеет status `supported`, when Visitor открывает её источники, then видит только прошедшие review Evidence; один URL без review не маркирует relation как `supported`.
5. Given relation имеет status `unverified`, when Visitor просматривает её, then отсутствие подтверждения явно обозначено и не маскируется отсутствием блока источников.
6. Given relation имеет status `disputed`, when Visitor просматривает её, then разногласие явно обозначено и доступны прошедшие review противоречащий материал и объяснение.
7. Given опубликована симметричная `overlaps_with`, when любая сторона отображает relation, then пользователь видит одну и ту же связь без необходимости хранить обратный дубликат.
8. Given связанный Genre ещё не имеет реализованного публичного route, when Visitor видит relation, then название не является неработающей ссылкой.
9. Given Genre или relation остаётся draft, when анонимный Visitor пытается получить его через public page/API, then содержание не раскрывается и возвращается публичное состояние «не найдено».
10. Given первая версия seed, when приложение развёрнуто в чистом окружении, then Genre Swing, Jazz и Jump Blues загружаются воспроизводимо без Performer, Group и Recording.
11. Given первая версия seed, when данные загружены, then она содержит полные опубликованные Claims `Swing developed_from Jazz` и `Swing contributed_to_emergence_of Jump Blues` с прошедшим review Evidence из утверждённых институциональных источников.
12. Given GenreRelation содержит subject, target и relation type, when Editor сохраняет её без остальных полей, then draft сохраняется и остаётся недоступным Visitor.
13. Given draft GenreRelation заполнена не полностью, when запрошена её публикация, then переход отклоняется с указанием отсутствующих обязательных данных.
14. Given опубликованный Swing, when Visitor загружает страницу, then overview, relations и sources получаются тремя отдельными API operations без N+1 requests по каждой relation или Source.
15. Given overview успешно загружен, when relations или sources operation завершается технической ошибкой, then основной Genre content остаётся доступен, а сбой показан как явная локальная ошибка секции, а не как пустые данные.

## Данные и контракты в области изменения

- Genre identity и metadata;
- Genre relation как специализированный Claim;
- temporal/geographic context, provenance и evidence roles relation;
- Evidence и Source projection для relation;
- public Genre overview, relations и sources queries/API;
- UI страницы и empty/error/loading states;
- воспроизводимый seed/import.

Точная схема хранения, endpoint, DTO, URL и миграция будут описаны после утверждения story. Этот документ не утверждает ORM или transport.

## In scope

- один работающий public Genre vertical slice;
- все поля и relation types, уже принятые для Genre;
- отсутствие и частичное заполнение каждой секции;
- evidence status и public visibility;
- controlled seed/import.

## Out of scope

- локализация UI и редакционного контента, locale negotiation и fallback;
- страницы и seed Performer, Group, Recording;
- переходы на detail pages других Genre;
- карта, списки, поиск и Stories content;
- формы Editor и полный editorial workflow;
- RAG, MCP и AI proposals;
- streaming integrations;
- локализованные URL и SEO-slugs.

## Ошибки и права

- Visitor читает только опубликованное.
- Неизвестный, архивный или непубличный Genre не различаются во внешнем ответе и дают состояние «не найдено».
- Genre overview является обязательной projection: его сбой даёт общую ошибку страницы.
- Relations и sources загружаются независимо. Их технический сбой не скрывает overview и не маскируется как пустая секция: UI показывает inline error/retry в границе секции.
- Между тремя отдельными reads не обещан общий database snapshot. Каждый response самосогласован и применяет public visibility на момент своего чтения.

## Зависимости

- [DDD Workshop 001](../../../domain/workshops/001-relationships-and-observations.md);
- [DDD Workshop 004](../../../domain/workshops/004-aggregate-boundaries.md);
- [DDD Workshop 005: публикация и видимость](../../../domain/workshops/005-publication-and-visibility.md);
- [UI contract](ui.md) утверждён;
- [Data/API workshop](data-api-workshop.md) утверждён;
- [OpenAPI contract](../../../api/openapi.yaml) `0.2.0` актуализирован после разделения page projections.

## Решено в data contract

- Приблизительный temporal context имеет редакционный `label` и optional structured bounds с precision.
- Geographic context в STORY-001 имеет text-first `summary`; Place catalog не вводится.

## История изменений

- 2026-08-16: по решению Product Owner локализация удалена из EPIC-001. Требования `FR-013`, `FR-014`, `NFR-001`, locale/fallback acceptance criterion и localized data scope сняты и не переиспользуются; тема перенесена в deferred scope.
- 2026-08-16: подтверждены минимальная публикация Genre, скрытие пустых секций и seed Swing/Jazz/Jump Blues; добавлен `FR-015` о полной GenreRelation.
- 2026-08-16: `FR-015` уточнён — draft relation допускает частичное заполнение, publish требует полноты; независимая публикация подтверждена.
- 2026-08-16: подтверждено повторное появление relation после повторной публикации endpoint; `confidence` удалён; review/publish permissions оставлены Editor до появления Reviewer.
- 2026-08-16: подтверждены два seed Claims и Smithsonian/Library of Congress Evidence; STORY-001 переведена в `accepted`.
- 2026-08-16: UI contract утверждён; точные spacing values оставлены на visual calibration при сохранении контракта читаемости и адаптивности.
- 2026-08-16: DQ-API-01–09 подтверждены; API использует Genre ID, slug отложен как web-route concern. Первоначально был принят один атомарный page response; решение заменено 2026-08-17.
- 2026-08-16: DQ-API-10 решён без нового поля: `explanation` disputed relation описывает суть разногласия; утверждён OpenAPI `0.1.0`.
- 2026-08-17: утверждена первая декомпозиция STORY-001 и создание новых перечисленных tests, включая полный E2E; перед Genre UI добавлен отдельный design checkpoint.
- 2026-08-17: единый `GenrePageResponse` заменён тремя projections: overview, relations и sources; добавлены `FR-016`, `AC-14` и `AC-15`, а ошибки relations/sources стали локальными ошибками секций.
- 2026-08-19: TASK-009 прогон приёмки записан в [acceptance.md](acceptance.md) (`draft` до утверждения Product Owner).
- 2026-08-17: каждая из трёх API operations выделена в свою техническую task; актуальная декомпозиция содержит девять tasks.
