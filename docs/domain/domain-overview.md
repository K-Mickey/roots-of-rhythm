# Черновой обзор предметной области

Статус: `draft`

Документ фиксирует концепты для следующего этапа DDD — построения ubiquitous language и context map. Он не является схемой БД.

## Принятые bounded contexts

### People Catalog

Владеет общей идентичностью физического Person: стабильным PersonId, canonical name, aliases, базовыми датами жизни с provenance, внешними идентификаторами и разрешением дублей.

People Catalog не владеет музыкальными или танцевальными ролями и исторической интерпретацией. Performer является музыкальной ролью Person, а будущие Dancer и Choreographer — ролями Dance Catalog.

### Music Catalog

Владеет музыкальными сущностями и фактическими metadata:

- Genre, Style и ClassificationConcept;
- Group;
- MusicalWork, Recording и Release;
- RecordingCredit и GroupMembership, ссылающимися на PersonId;
- ClassificationAssignment;
- Place, Period и каноническими внешними идентификаторами музыкальных сущностей;
- ссылки на MediaAsset, которым владеет общий supporting capability Media Management; это не отдельный bounded context.

В MVP MusicalWork и Release могут иметь ограниченную реализацию, но не должны смешиваться с Recording. Одно MusicalWork может иметь несколько Recording.

Person и Group нельзя сводить к одному `Artist`: Group имеет самостоятельную идентичность, а membership и credit обладают собственным смыслом и периодом. `Artist` допустим только как внешний или пользовательский собирательный термин.

### Dance Catalog

Владеет идентичностью Dance, названиями, aliases, терминами и базовыми описательными metadata. В будущем может владеть ролями Dancer/Choreographer, школами, событиями и отношениями между Dance, ссылаясь на PersonId.

Исторические Claims и DanceGenreRelation не принадлежат Dance Catalog. MVP не оценивает танцевальность Genre или Recording; Style показывается через классификацию связанных Genre и Recording.

### Historical Knowledge

Владеет интерпретацией и объяснением истории:

- Claim и его специализированными kinds;
- Evidence и Source;
- Genre relations, Influence и DanceGenreRelation;
- Story, StorySection и NarrativeEntityReference;
- редакционными объяснениями и степенью уверенности.

Historical Knowledge ссылается на стабильные IDs People Catalog, Music Catalog и Dance Catalog, но не владеет их identity metadata.

## Сквозные capabilities

Editorial workflow, Discovery queries и AI Research нужны продукту и получают явные логические границы, но не являются bounded contexts, сервисами или заранее утверждёнными code modules:

- Editorial задаёт требования draft/review/publish, authorization и audit;
- Discovery собирает read-only карту, поиск, списки и составные страницы;
- AI Research оркестрирует ingestion, RAG, MCP и agent proposals через обычные application use cases.

Editorial владеет оркестрацией и аудитом, но не копирует доменный статус. Discovery владеет только перестраиваемыми read models. Historical Knowledge владеет Source и Evidence, тогда как AI Research владеет производными chunks/indexes, runs, evaluation и proposals.

Их package boundaries определяются application architecture и реальными stories. Пустые модули заранее не создаются. Полная политика: [границы Editorial, Discovery и AI Research](supporting-capabilities.md).

Media Management является соседней supporting capability: он хранит identity, provenance и rights metadata MediaAsset, а также технические MediaReference внешних streaming providers. Contexts используют стабильный MediaAssetId; MediaReference ссылается на RecordingId, но не становится частью Recording aggregate. Принятая граница описана в [Media Management](media-management.md).

## Центральный концепт Claim

Историческое влияние и значение часто являются интерпретацией, а не простым фактом. Поэтому содержательная связь моделируется как проверяемое утверждение:

```text
Claim
├── subject
├── predicate
├── object или literal
├── explanation
├── temporal_context
├── geographic_context
├── editorial_status
├── evidence_status: unverified | supported | disputed
├── evidence[] с ролью supports | opposes | context
└── provenance
```

Связь карты может быть проекцией опубликованных Claims, а не самостоятельным ребром. Неподтверждённая связь допустима, но обязана визуально отличаться от `supported` и не должна молча попадать в подтверждённый RAG-корпус.

## Как отвечать на сложные вопросы

### «Чем jump blues отличается от swing?»

Ответ формируется тремя способами:

1. Структурированные атрибуты и Claims на страницах жанров.
2. Редакционная Story типа comparison.
3. RAG-ответ, который синтезирует только подтверждённый корпус и приводит цитаты.

RAG не заменяет редакционный материал: Story даёт стабильный авторский маршрут, RAG отвечает на вариативный вопрос.

### «Как swing превратился в rhythm and blues и rock and roll?»

Одного текстового поля Genre.description недостаточно. Нужны:

- несколько направленных Transition или Influence Claims;
- временные и географические контексты;
- исполнители и записи, демонстрирующие каждый шаг;
- Story или Journey, собирающая ветвящийся граф в понятную последовательность;
- возможность открыть содержание ребра карты.

### «Почему исполнитель или запись важны?»

Историческое значение хранится не как один глобальный комментарий и не как отдельная сущность для значимости, а как набор Claims с `claim_kind=significance`, contribution types и явным evidence status. Страница Recording нужна в MVP; страницы MusicalWork и Release являются естественным расширением.

### «Кто повлиял на исполнителя?»

Ответ строится из направленных Influence Claims между Performer, Group, Genre, Scene или музыкальными практиками. Каждая связь имеет объяснение, период, evidence status и editorial status; Evidence может отсутствовать и тогда связь явно помечена `unverified`. Простого списка имён недостаточно.

### «Какие музыкальные признаки можно услышать в записи?»

Ответ является структурированным listening guide: музыкальный признак, понятное объяснение, контекст и опциональный временной диапазон. ListeningObservation требует авторства и audit timestamp, но не внешнего Evidence. Историческое обобщение на его основе оформляется отдельным Claim.

## Участие, состав и credits

```text
GroupMembership
├── performer
├── group
├── period
├── roles_or_instruments[]
├── evidence[]
└── editorial_status

RecordingCredit
├── recording
├── performer_or_group
├── credited_as optional
├── roles_or_instruments[]
├── billing_role
├── evidence[]
└── editorial_status
```

Credit Recording и membership Group — разные факты. Человек мог участвовать в конкретной записи, не являясь постоянным участником группы; группа могла быть создана только для студийной сессии. Для публикации Recording требуется один primary credit, но полный состав, точные функции и Evidence не обязательны. Group может быть опубликована без известного состава. Даты отношений допускают неполную точность и `circa`; вычисляемые этапы карьеры не хранятся отдельными строками.

Release в будущем получает собственные ReleaseCredit: основной артист издания, producer, label и другие роли не обязаны совпадать с составом каждой Recording.

## Изображения

Изображение рассматривается как управляемый `MediaAsset`, а не как строковый URL внутри Performer или Genre:

```text
MediaAsset
├── source
├── rights_or_license
├── attribution
├── alt_text
├── role: primary | thumbnail | gallery | cover
├── focal_point optional
└── editorial_status
```

Связь MediaAsset с объектом позволяет одному объекту иметь разные изображения и одному разрешённому материалу использоваться в нескольких контекстах. Точная модель хранения и производных превью принимается позднее ADR.

## Связь жанров

Genre не имеет единственного parent. Отношение должно допускать:

- несколько источников влияния;
- несколько последующих направлений;
- параллельное развитие;
- период и географию;
- спорность;
- объяснение и музыкальные примеры.

PostgreSQL-таблицы отношений достаточно для MVP. Решение о графовой БД принимается только по измеренной потребности.

Минимальный enum отношений: `influenced`, `contributed_to_emergence_of`, `developed_from`, симметричный `overlaps_with` и `revival_of`. Эти значения различают причинность и исторический смысл, а не силу влияния. `fused_with` выражается несколькими причинными связями и объясняющим Claim.

Классификация Group, Release, MusicalWork и Recording независима и допускает несколько Genre/Style. Scene требует периода, места, участников и совместных практик; Tradition — подтверждаемой преемственности. Полная политика описана в [политике музыкальной классификации](classification-policy.md).

## Состояние Domain Discovery

Workshop 001–004 определили классификацию, исторические связи, DanceGenreRelation, Context Map и aggregate boundaries. PracticeFit и DanceRecordingFit не являются терминами MVP и не возвращаются без отдельного пользовательского сценария и проверяемой методологии.

Базовый Domain Discovery завершён: Media Management и ADR-0002/0003 приняты. На этапе первой user story открыт узкий [DDD Workshop 005](workshops/005-publication-and-visibility.md) о независимом lifecycle GenreRelation и вычисляемой публичной видимости. Точные Story types и остальные Editorial rules уточняются соответствующими user stories, а не новым универсальным domain workshop.
