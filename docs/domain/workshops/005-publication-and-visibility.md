# DDD Workshop 005: публикация и публичная видимость

Статус: `accepted`

Цель: определить взаимодействие `editorial_status` Genre и GenreRelation без каскадной публикации разных aggregates и без раскрытия draft-данных.

## Подтверждённые входные решения

- Genre и Claim/GenreRelation являются разными Aggregate Roots.
- Для публикации Genre достаточно минимального содержательного набора; остальные данные дополняются позже.
- Draft GenreRelation допускает постепенное заполнение. Для создания обязательны только subject Genre, target Genre и relation type; остальные содержательные поля можно дополнить позже.
- Публичная relation не должна раскрывать непубличный Genre.

## Вариант A: каскадная публикация relations вместе с Genre

Команда `publish_genre` публикует Genre и все связанные relations.

Преимущество: одна операция редактора сразу делает страницу полной.

Проблемы:

- Genre и Claim являются разными aggregates с независимым review;
- у Genre может быть неограниченное число входящих и исходящих Claims;
- непонятно, какой Genre владеет симметричной `overlaps_with`;
- публикация одного Genre может неожиданно раскрыть утверждение о другом;
- откат и частичная ошибка требуют распределённого изменения нескольких aggregates.

Вердикт: отклонить как нарушение уже принятых aggregate boundaries.

## Вариант B: независимая публикация, целостность только на ответственности Editor

Editor вручную следит, что оба Genre опубликованы, а public query доверяет статусу relation.

Преимущество: простые write-команды.

Проблемы:

- человеческая ошибка создаёт broken reference или раскрывает identity draft Genre;
- разные public queries могут реализовать проверку непоследовательно;
- безопасность публичного корпуса становится организационным правилом вместо системного инварианта.

Вердикт: отклонить. Editor отвечает за содержание, но не должен быть единственной защитой публичной целостности.

## Вариант C: независимый lifecycle и вычисляемая публичная видимость

Предлагаемое решение:

1. `publish_genre` изменяет только Genre.
2. `publish_genre_relation` изменяет только Claim/GenreRelation.
3. Публикация relation разрешена, только если relation полностью заполнена и оба endpoint Genre в этот момент опубликованы.
4. Public Discovery показывает relation, только если одновременно опубликованы relation, subject Genre и target Genre.
5. Архивирование или снятие с публикации любого endpoint немедленно скрывает relation из public read model без изменения самой relation.
6. Повторная публикация endpoint снова делает ранее опубликованную relation видимой, если её собственный статус и содержание не изменились.
7. Editor видит вычисляемую причину невидимости, например `endpoint_not_published`; это не новый доменный `editorial_status`.

Формула:

```text
publicly_visible(relation) =
  relation.editorial_status == published
  AND subject.editorial_status == published
  AND target.editorial_status == published
```

### Почему две проверки

Проверка в publish command даёт осмысленность перехода в `published`. Проверка в read path защищает от последующего архивирования endpoint, гонки или ошибки импорта. Это не дублирование бизнес-истины: write-side проверяет допустимость команды, read-side вычисляет текущую видимость.

## Полнота GenreRelation

Для создания draft обязательны:

- существующие и различные subject/target Genre IDs;
- один relation type из принятого enum;
- автоматически установленные `editorial_status=draft` и audit author/time.

Остальные поля draft опциональны и не получают фиктивных defaults. Editor может сохранить draft и вернуться к нему.

Для публикации relation обязательны:

- содержательное explanation;
- temporal context, допускающий приблизительные границы;
- geographic context подходящей точности;
- явно заданный `evidence_status`;
- provenance;
- Evidence по условным правилам статуса.

`confidence` исключён из Claim MVP как субъективное поле без определённой шкалы и уникального пользовательского сценария.

Условные правила Evidence остаются прежними:

- `unverified` допускает отсутствие прошедшего review Evidence;
- `supported` требует минимум одно прошедшее review Evidence с ролью `supports`;
- `disputed` требует прошедшее review Evidence с ролью `opposes` и объяснение разногласия.

Пустые строки, фиктивные `unknown` и технические defaults не считаются заполнением. Неполный draft хранится, но перейти в `published` не может.

## Смысл editorial status

- `draft` — relation создана и может быть заполнена частично; Visitor её не видит;
- `in_review` — материал передан на редакционную проверку; обязательность полной готовности для этого перехода определяется в EPIC-005;
- `published` — содержание одобрено; фактическая публичная видимость дополнительно зависит от обоих endpoint Genre;
- `archived` — relation намеренно выведена из актуального корпуса и никогда не показывается публично.

Переходы не публикуют и не архивируют соседние aggregates. `in_review` является состоянием материала и само по себе не требует отдельного человека с ролью Reviewer. Точные роли, разрешённые переходы, versioning опубликованного материала и audit events относятся к EPIC-005. Controlled seed первой story обязан пройти те же publication invariants, даже если технически выполняется доверенным bootstrap-процессом без Editor UI.

## Проверка devil's advocate

### Failure mode: endpoint архивирован после relation

Факт: отдельные aggregates меняются независимо.

Сценарий: Jazz архивирован, но relation остаётся `published`.

Защита: public visibility gate скрывает relation; Editorial показывает вычисляемую блокировку. Каскадное изменение Claim не требуется.

### Failure mode: одновременная публикация

Факт: проверка другого aggregate может устареть до commit.

Сценарий: relation проверила опубликованные endpoints, один из них одновременно архивирован.

Защита: транзакционная проверка в общей БД для publish command и обязательная повторная фильтрация read path. Точный locking strategy определяется реализацией, а не domain workshop.

### Failure mode: повторная публикация возвращает старую relation

Факт: скрытая relation не архивируется автоматически.

Сценарий: Genre существенно переработали и опубликовали снова; прежняя relation автоматически вернулась в public projection.

Компромисс MVP: допустимо, пока редактирование опубликованного Genre не использует отдельные версии. Перед введением draft-copy/versioning EPIC-005 должен определить, какие изменения инвалидируют review зависимых Claims.

### Failure mode: `confidence` дублирует evidence status

Факт: evidence status описан строго, а шкала confidence ещё не определена.

Сценарий: Editor выставляет `high` для `unverified`, пользователь получает противоречивый сигнал.

Решение: `confidence` исключён из Claim MVP. Поле не попадает в API contract или persistence model.

## Что предполагалось под confidence

`confidence` попал в ранний черновик Claim как предполагаемая оценка уверенности автора или редактора в точности формулировки. Для него не были определены enum, шкала, правила вычисления, пользовательское отображение или уникальный сценарий.

Это отличается от `evidence_status` теоретически:

- evidence status отвечает, прошли ли поддерживающие или противоречащие материалы review;
- confidence мог бы выражать субъективную уверенность в интерпретации даже при одинаковом наборе Evidence.

На практике сочетания вроде `confidence=high + evidence_status=unverified` или `confidence=low + evidence_status=supported` трудно объяснить Visitor и Editor. Числовая уверенность модели или retrieval score также не принадлежит Claim: это техническая metadata AI Research run.

Product Owner подтвердил удаление `confidence` из Claim MVP. Вернуть термин можно только с отдельным пользовательским сценарием, определённой шкалой и правилами сочетания с evidence status.

## Принятое решение

Product Owner подтвердил вариант C: независимая публикация Genre и GenreRelation плюс системно вычисляемая публичная видимость. Не вводить cascade, event bus, новый visibility status или ответственность Editor как единственный guard.

## Итоговые решения

1. Genre и GenreRelation публикуются независимо; каскад запрещён.
2. Public visibility relation вычисляется из её статуса и статусов обоих endpoint Genre.
3. Архивирование endpoint скрывает relation без изменения Claim.
4. Повторная публикация endpoint снова показывает ранее опубликованную неизменённую relation без повторного review.
5. Draft relation требует только subject, target и relation type; publish требует полной содержательной формы.
6. `confidence` исключён из Claim MVP.
7. В MVP Editor получает review/publish permissions; отдельный Reviewer/Moderator отложен.

Решения подтверждены Product Owner 2026-08-16.
