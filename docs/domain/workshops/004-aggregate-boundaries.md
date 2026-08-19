# DDD Workshop 004: агрегаты, инварианты и транзакции

Статус: `accepted`

Цель: определить минимальные границы согласованности внутри принятых contexts. Workshop не проектирует таблицы, ORM-модели, repositories, endpoints или структуру директорий.

## Что здесь означает Aggregate

Aggregate — минимальная группа объектов, чьи инварианты должны соблюдаться одной командой и одной транзакцией. Aggregate Root является единственной точкой изменения этой группы.

Aggregate не означает:

- экран или JSON целиком;
- всё, что показывается на одной странице;
- всю связанную историческую сеть;
- bounded context, module или service;
- обязательную ORM-модель на каждый термин.

Страница Performer может читать Person, GroupMembership, Recording, Claims и ClassificationAssignments, но это не превращает их в один aggregate.

## DQ-01. Какой общий принцип границ принимаем?

### Рекомендация

1. Одна пользовательская команда изменяет один aggregate, если нет явно названного межагрегатного сценария.
2. Внутри aggregate хранятся только данные, необходимые для его локальных инвариантов.
3. Другие aggregates и другие contexts упоминаются по стабильному ID.
4. Неограниченно растущие коллекции и независимо редактируемые отношения не включаются в родительский aggregate.
5. Составная страница собирается Discovery queries и не определяет транзакционную границу.
6. DB constraints защищают простые инварианты уникальности; доменная модель защищает смысловые переходы.

### Пример

Публикация Recording должна атомарно проверить её обязательные metadata и наличие primary credit. Но публикация Recording не должна в той же транзакции публиковать Person, Group, Genre и связанные Claims.

### Отвергнутый вариант

Один большой `MusicGraph` или `Catalog` aggregate сделал бы любую правку жанра, записи или участника частью одной логической блокировки. Он не отражает пользовательские команды и не масштабируется даже внутри обычной реляционной БД.

## DQ-02. Какие aggregates нужны каталогам?

### People Catalog

`Person` принят как Aggregate Root. Внутри него находятся canonical name, aliases, базовые даты и внешние identity IDs, потому что merge/split и защита от дублей требуют согласованной identity.

Не входят в Person:

- GroupMembership;
- RecordingCredit;
- Claims;
- пользовательский аккаунт;
- будущие роли Dancer или Choreographer.

Публикация Person требует canonical name. Даты могут быть неполными или приблизительными. Alias не может бесшумно стать второй Person; глобальная дедупликация остаётся отдельным application use case с DB-проверками.

### Music Catalog

| Предлагаемый Aggregate Root | Что находится внутри | Что хранится отдельно |
|---|---|---|
| `ClassificationConcept` | kind, canonical name, aliases, определение, границы и статус | assignments и исторические relations |
| `Group` | identity metadata, aliases, период существования и статус | memberships, recordings, Claims |
| `MusicalWork` | identity произведения, названия, авторские metadata доступной глубины | recordings и releases |
| `Recording` | metadata исполнения, ссылка на MusicalWork и ограниченная коллекция RecordingCredit | classifications, Claims, releases |
| `Release` | metadata издания и упорядоченные Track | Recording и их credits |
| `GroupMembership` | PersonId, GroupId, период, роли/инструменты, provenance и статус | Person и Group целиком |
| `ClassificationAssignment` | target ID/type, concept ID, explanation или claim_id, provenance, evidence/editorial status | target и concept целиком |

`RecordingCredit` является дочерней Entity внутри Recording, а не отдельным Aggregate Root. Причина: минимальный инвариант публикации Recording — хотя бы один `billing_role=primary`; добавление, удаление и проверка credits должны быть согласованы с Recording. Количество credits одной Recording естественно ограничено.

`GroupMembership` является отдельным aggregate: состав группы меняется независимо, может быть неполным и со временем образует растущую коллекцию. Group публикуется без полного состава.

`ClassificationAssignment` также отдельный aggregate: это независимо редактируемая many-to-many связь со своим provenance и lifecycle. Изменение назначения не перепубликует Person, Group или Recording.

Публикация assignment требует explanation или claim_id, provenance и опубликованные target и concept. До появления owned evidence references публиковать можно только `evidence_status=unverified`; `supported` и `disputed` можно хранить в draft.

`Track` остаётся дочерней Entity Release: порядок дорожек и отсутствие двух позиций с одинаковым номером являются локальным инвариантом конкретного издания. Полноценная реализация Release отложена, но граница не смешивает Track с Recording.

### Dance Catalog

`Dance` принят как Aggregate Root со своей identity, aliases, базовыми metadata и статусом. DanceGenreRelation, Claims, Performer и Recording в него не входят.

Будущие Dancer/Choreographer и события не добавляются внутрь Dance автоматически: для них потребуется отдельная команда и проверка границ на реальных сценариях.

## DQ-03. Какие aggregates нужны Historical Knowledge?

### Claim

`Claim` принят как Aggregate Root. Внутри находятся:

- subject и object/literal references;
- claim kind и специализированные значения вроде HistoricalRole;
- explanation, temporal и geographic context;
- editorial status и evidence status;
- небольшая коллекция `ClaimEvidenceReference`.

DanceGenreRelation и GenreRelation являются специализированными видами Claim, а не отдельными независимыми aggregates. Это сохраняет общие правила публикации, Evidence и спорности.

`ClaimEvidenceReference` ссылается на SourceFragment и содержит роль Evidence: `supports`, `opposes` или `context`. Он находится внутри Claim, чтобы изменение evidence status и удаление последнего подтверждающего Evidence не расходились.

Предлагаемые инварианты:

- `supported` требует хотя бы один прошедший review reference с ролью `supports`;
- `disputed` требует прошедший review материал с ролью `opposes` и объяснение разногласия;
- `unverified` может не иметь Evidence или иметь ещё не проверенные references;
- публикация Claim допустима при любом из трёх evidence statuses, но UI и RAG соблюдают уже принятые различия;
- симметричный `overlaps_with` хранится один раз в каноническом порядке IDs.

### Source и его версии

`Source` принят как Aggregate Root для bibliographic metadata, rights/access policy и identity источника. `SourceVersion` является отдельным Aggregate Root, ссылающимся на SourceId: версия имеет собственный ingestion lifecycle и после одобрения не изменяет извлечённое содержание задним числом.

`SourceFragment` является отдельным Aggregate Root, ссылающимся на SourceVersionId. Причина — количество фрагментов не ограничено, они создаются пакетно и независимо используются многими Claims и retrieval chunks. Фрагмент не владеет Evidence links обратно к Claims.

Изменение опубликованной версии создаёт новую SourceVersion, а не переписывает locators уже использованного Evidence. Точные права хранения текста определяются отдельной security/legal story.

### Story и ListeningGuide

`Story` принят как Aggregate Root с упорядоченными StorySection и NarrativeEntityReference внутри. Story является ограниченным редакционным документом; публикация должна атомарно проверять порядок секций и разрешимость обязательных ссылок.

`ListeningGuide` принят как отдельный Aggregate Root Historical Knowledge, ссылающийся на RecordingId и содержащий небольшую упорядоченную коллекцию ListeningObservation. Автор и audit timestamp обязательны для каждого наблюдения; временной диапазон опционален и должен находиться в пределах известной длительности Recording, если длительность доступна.

Контекстная заметка о Recording внутри Story остаётся NarrativeEntityReference и не становится глобальным ListeningObservation.

## DQ-04. Являются ли supporting capabilities агрегатами?

Нет: capability или module сам по себе не aggregate.

### Editorial

- `EditorialAction` — неизменяемая audit record, не доменная точка изменения контента;
- `ReviewNote` может иметь собственный lifecycle, но не владеет объектом review;
- `EditorialQueueItem` — производная read model;
- статус публикации остаётся внутри Aggregate Root context-владельца.

### Discovery

Discovery не имеет write-side aggregates. `SearchResult`, `MapNode`, `HomeStatistics` и другие модели полностью производны и перестраиваемы.

### AI Research

- `IngestionJob`, `RetrievalRun`, `AgentRun`, `EvaluationRun` и `AIProposal` могут быть независимыми operational roots со своим коротким lifecycle;
- `EmbeddingRecord`, `IndexEntry` и `RetrievalChunk` являются перестраиваемыми техническими записями, а не доменными aggregates;
- `CorpusAdmission` фиксирует включение версии/фрагмента в корпус и editor audit, но не меняет Source, Claim или их evidence status;
- принятие AIProposal вызывает application use case владельца и создаёт новый draft; proposal не превращается в опубликованный объект на месте.

Конкретные operational roots создаются только с первой использующей story. Пустая иерархия AI-классов заранее не нужна.

## DQ-05. Как соблюдать межагрегатные инварианты без event bus?

### Синхронная модель MVP

1. Application use case загружает изменяемый Aggregate Root.
2. Необходимые внешние факты проверяются через query/application contracts владельцев.
3. Root проверяет свои локальные инварианты и выполняет переход.
4. Изменение сохраняется одной DB transaction.
5. Discovery читает актуальные данные напрямую либо перестраиваемую projection.

Event bus для этого не нужен. Если операция требует изменить два aggregates, сначала проверяется, действительно ли это один пользовательский инвариант. Если да, application service может координировать две записи в одной локальной DB transaction, но такая операция документируется явно и не становится правилом по умолчанию.

Для сильного кандидата на отдельный process/service запрещено создавать новый инвариант, зависящий от общей ORM session или атомарной записи в данные двух владельцев. Такая граница использует идемпотентные шаги и явное состояние workflow уже внутри монолита. Это не делает все внутренние вызовы асинхронными и не требует очереди.

### Ссылочная целостность

- новый Claim, credit, membership или assignment ссылается только на существующий стабильный ID;
- публикация проверяет, что обязательные references разрешимы и доступны целевой публичной аудитории;
- опубликованный объект, на который ссылается другой опубликованный материал, не удаляется физически обычным редакционным действием — используется archive и стабильный ID;
- archive связанного объекта не публикует каскадные изменения автоматически;
- поведение UI при архивной ссылке и точная delete policy уточняются в editorial stories.

### Конкурентные изменения

На старте достаточно DB transactions, unique constraints и обнаружения конфликтующего обновления. Политика optimistic locking вводится только если реальный редакторский сценарий показывает риск потери параллельных правок.

### Примеры транзакционных границ

| Команда | Одна транзакция | Не происходит автоматически |
|---|---|---|
| Опубликовать Recording | Recording и его credits | публикация Person, Group, Claims и assignments |
| Добавить GroupMembership | новая membership и проверка IDs/периода | изменение Group или Person |
| Поддержать Claim Evidence | Claim и его evidence references/status | изменение SourceFragment |
| Опубликовать Story | Story, sections и narrative references | публикация всех упомянутых Claims |
| Принять AIProposal | создание draft атомарно у context-владельца; отдельная идемпотентная отметка proposal с draft ID | общая транзакция AI Research и доменного context, публикация draft |

## Предлагаемый минимальный набор Aggregate Roots MVP

```text
People Catalog:        Person
Music Catalog:         ClassificationConcept, Group, MusicalWork, Recording,
                       GroupMembership, ClassificationAssignment
Dance Catalog:         Dance
Historical Knowledge: Claim, Source, SourceVersion, SourceFragment, Story,
                       ListeningGuide
Supporting:            только operational roots, реально нужные первой story
Deferred:              публичная страница Track; полный мировой каталог переизданий
```

Это список границ согласованности, а не требование реализовать все roots до первого vertical slice.

## Принятые решения

1. Принят принцип малых aggregates и ссылок по ID вместо общего графового aggregate.
2. `RecordingCredit` входит в Recording; GroupMembership и ClassificationAssignment являются самостоятельными aggregates.
3. Claim владеет Evidence references; Source, SourceVersion и SourceFragment являются отдельными roots.
4. Story владеет секциями; ListeningGuide отдельно владеет наблюдениями.
5. По умолчанию одна транзакция изменяет один aggregate; синхронная межагрегатная оркестрация является явным исключением; event bus не используется.

Решения приняты пользователем 2026-08-15. Основные критерии — атомарность инвариантов и баланс размера aggregates.

Уточнение 2026-08-15: межагрегатная локальная транзакция не используется для связи домена с сильным кандидатом на отдельный процесс. AIProposal принимается двухшагово и идемпотентно; это исправляет конфликт с направлением будущего выделения AI Research.

Уточнение 2026-08-19 (STORY-005): ClassificationAssignment хранит explanation или claim_id; публикация требует provenance и published endpoints; до evidence references публикуется только `unverified`.
