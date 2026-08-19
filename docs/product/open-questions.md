# Открытые продуктовые вопросы

Статус: `draft`

Владелец решений: Product Owner.

## Блокирующие перед соответствующими epics

Вопросы не блокируют утверждение всей epic map одновременно. Каждый должен быть закрыт перед формализацией использующей story.

### EPIC-001/002/004 — публичные страницы

1. Какие конкретные жанры входят в стартовые 6–10 и подтверждается ли Swing первым?
2. Для каких типов сущностей основное изображение обязательно, если оно вообще обязательно? Для Performer в STORY-005: не обязательно; секция скрыта; MediaAsset не входит в срез. Остальные типы — по-прежнему открытый вопрос.

### EPIC-005 — Editorial

6. Нужна ли публичная регистрация в MVP или только вручную созданные editor-аккаунты?
7. Нужна ли draft-копия при редактировании уже опубликованного материала?
8. Какая delete/archive policy применяется к опубликованным и связанным объектам?

### EPIC-006/008 — RAG и AI Research

9. Какие источники разрешено хранить полностью, а для каких только metadata, locator и ограниченный фрагмент?
10. Какие критерии качества должны быть достигнуты для пяти ключевых вопросов без RAG и с RAG?

### EPIC-011 — Stories

11. Какие типы историй обязательны в MVP: article, comparison, timeline, journey?

## Можно решить позднее

### Отложенная локализация

3. Какое поведение применять при отсутствии запрошенного опубликованного перевода: явный fallback на язык проекта или состояние «перевод недоступен»?
4. Нужны ли локализованные URL и SEO-slugs?
12. Как хранить локализованный редакционный контент: типизированными translation entities, JSON-документом на локаль или в отдельном Content aggregate?

Эти вопросы не блокируют EPIC-001 и возвращаются только при создании отдельной localization story.

- страницы MusicalWork, Release и Album;
- танцоры и связи между танцами;
- школы, события и география танцевальных сцен;
- пользовательские коллекции;
- независимая роль Reviewer;
- персональные рекомендации;
- графовая БД;
- отдельные карты танцев и исполнителей.
- конкретные media providers завершающего этапа MVP;
- варианты монетизации после подтверждения продуктовой ценности.
- временные шкалы и карты карьеры Performer;
- расширенные credits Recording и Release;
- тексты MusicalWork, переводы и аннотации;
- галереи и архивные MediaAsset;
- механизм определения и показа знаковых материалов.

## Закрытые вопросы

### Какие Genre relations входят в первый seed?

Решение: `Swing developed_from Jazz` и `Swing contributed_to_emergence_of Jump Blues`. Smithsonian и Library of Congress приняты как Evidence; конкретные фрагменты проходят обычный editorial review. Прямой Jazz ↔ Jump Blues и искусственное покрытие всех enum не добавляются.

Основание: [исследование seed relations](../research/seed-genre-relations.md) и [STORY-001](../specs/epic-001-genre-exploration/story-001-view-published-genre/README.md).

### Кто выполняет review и публикацию в MVP?

Решение: Editor получает review/publish permissions и может публиковать собственный материал. Отдельный Reviewer/Moderator и перераспределение прав откладываются до появления второго редактора или требования независимой проверки. Administrator управляет аккаунтами и ролями; отдельный Superadmin не вводится.

Основание: [аудитория и роли](personas-and-access.md) и [DDD Workshop 005](../domain/workshops/005-publication-and-visibility.md).

### Какие поля Performer обязательны для публикации в STORY-005?

Решение: обязателен только канонический name. Aliases, биография, даты жизни, external identities, ClassificationAssignment на Genre и изображение опциональны; пустые секции скрыты. Primary image для Performer не обязателен и в STORY-005 не загружается.

Основание: [STORY-005](../specs/epic-002-performer-group-recording/story-005-view-published-performer/README.md).

### Какой минимальный Genre seed используется в STORY-001?

Решение: controlled seed содержит Swing, Jazz и Jump Blues. Relations добавляются только после content research и не создаются искусственно ради покрытия enum.

Основание: [STORY-001](../specs/epic-001-genre-exploration/story-001-view-published-genre/README.md).

### Какие поля Genre обязательны для публикации и как показывать пустые секции?

Решение: обязательны только `name + definition`; остальные поля и коллекции опциональны. Visitor не видит пустые секции, а фиктивные defaults в данных запрещены.

Основание: [STORY-001](../specs/epic-001-genre-exploration/story-001-view-published-genre/README.md).

### Нужно ли закладывать backend-локализацию в первую Genre story?

Актуальное решение от 2026-08-16: нет. Локализация удалена из EPIC-001 и STORY-001 и перенесена в deferred scope. Первый vertical slice не содержит locale, translation, fallback или localized URL abstractions.

Предыдущее решение заложить backend-локализацию сразу отменено Product Owner после обсуждения стоимости хранения и joins. Исследование сохранено как вход для будущей localization story.

Основание: [отложенные возможности](future-scope.md), [исследование подходов к локализации](../research/localization-approaches.md) и [STORY-001](../specs/epic-001-genre-exploration/story-001-view-published-genre/README.md).

### Как развивается главная?

Решение 2026-08-19: три стадии в EPIC-010. HOME-0 — крупное название и короткое описание по центру, без жанров и дашборда, берётся сразу (STORY-003). Список всех жанров — отдельная страница каталога, не главная. HOME-1 — базовая с навигацией по существующим routes и `HomeStatistics`. HOME-2 — каталоги, поиск и вход на карту. Знаковые подборки остаются в deferred scope.

Основание: [эволюция главной](../specs/epic-010-home-search-catalog/home-evolution.md) и [границы MVP](mvp-scope.md).

### Является ли Recording полноценной публичной страницей MVP?

Решение: да. Recording является самостоятельным доказательным музыкальным примером. MusicalWork отделяется от Recording; сравнение разных записей одного произведения откладывается.

Основание: [глоссарий](../domain/glossary.md) и [границы MVP](mvp-scope.md).

### Когда выбирать и интегрировать музыкальных провайдеров?

Решение: на последнем этапе MVP. До этого система обязана поддерживать Recording и отсутствие playback-данных без нарушения пользовательского сценария.

Основание: [границы MVP](mvp-scope.md) и [исследование провайдеров](../research/media-providers.md).

### Какие credits и membership обязательны в MVP?

Решение: для публикации Recording требуется хотя бы один primary RecordingCredit на Performer или Group. Конкретная функция, instrument, полный состав и внешний Evidence опциональны. Group публикуется без известного состава; GroupMembership допускает неизвестные или приблизительные границы периода.

Основание: [DDD Workshop 001](../domain/workshops/001-relationships-and-observations.md).

### Обязателен ли внешний источник для публикации Claim?

Решение: нет. Публикация и подтверждённость разделены. Опубликованный Claim показывает `unverified`, `supported` или `disputed`; `supported` требует проверенного Evidence. Фактический RAG первой версии не использует `unverified` как основание ответа.

Основание: [DDD Workshop 001](../domain/workshops/001-relationships-and-observations.md) и [AI scope](../ai/ai-scope.md).

### Какие отношения Genre входят в MVP?

Решение: `influenced`, `contributed_to_emergence_of`, `developed_from`, симметричный `overlaps_with` и `revival_of`. Это типы исторического смысла и причинности, а не шкала силы. `fused_with` исключён: формирование третьего Genre выражается несколькими причинными связями и объясняющим Claim или Story.

Основание: [DDD Workshop 001](../domain/workshops/001-relationships-and-observations.md).

### Как поддерживаются Genre, Style, Scene и Tradition в MVP?

Решение: Genre является публичной сущностью и узлом основной карты. Style является структурированной классификацией и фильтром, но не требует отдельной страницы или узла карты. Scene и Tradition сначала моделируются Claims; отдельное ClassificationConcept создаётся только по принятым критериям и проверяемым сценариям использования. Тип и конкретное понятие разделены.

Основание: [политика музыкальной классификации](../domain/classification-policy.md) и [DDD Workshop 001](../domain/workshops/001-relationships-and-observations.md).

### Как MVP связывает Dance с музыкой?

Решение: только через исторический DanceGenreRelation с ролями `formative`, `core_historical_practice`, `documented_historical_use`. `authentic` является UI-представлением первых двух ролей, а не полем. DanceRecordingFit, PracticeFit и рейтинг танцевальности не входят в MVP; редакционные guides, экспертные подборки и пользовательское голосование сохранены как будущие гипотезы.

Основание: [DDD Workshop 002](../domain/workshops/002-dance-music-relations.md) и [future scope](future-scope.md).

### Какие Evidence и соревновательные правила нужны для DanceGenreRelation?

Решение: DanceGenreRelation является Claim с обязательными period/temporal context и explanation и использует общие статусы `unverified`, `supported`, `disputed`. Evidence обязательно для `supported`. CompetitionEligibility не входит в MVP и не планируется без нового пользовательского сценария.

Основание: [DDD Workshop 002, DQ-05](../domain/workshops/002-dance-music-relations.md).

## Принцип работы с вопросами

Закрывать вопрос отдельным решением, story clarification или ADR в зависимости от характера. Не удалять закрытый вопрос: переносить его в соответствующий документ и оставлять ссылку на решение.
