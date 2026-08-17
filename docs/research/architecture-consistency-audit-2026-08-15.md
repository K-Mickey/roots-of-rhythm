# Аудит согласованности архитектурных решений — 2026-08-15

Статус: `research`

Проверяемое утверждение: принятые SDD/DDD-решения позволяют начать с простого модульного монолита, сохраняют атомарность aggregates и не блокируют позднее выделение инфраструктурных процессов.

## Блокирующие расхождения

### AIProposal и общая транзакция

Факт: Workshop 004 предлагал одной транзакцией создать доменный draft и отметить AIProposal принятым. AI Research одновременно назван сильным кандидатом на отдельный процесс.

Сценарий отказа: после выделения AI Research общая ORM transaction исчезает; network timeout оставляет неизвестный результат и может создать два draft при retry.

Исправление: workflow разделён на атомарное идемпотентное создание draft у владельца и отдельную отметку proposal с draft ID. Проверка: повтор команды с тем же proposal ID возвращает тот же draft.

### Неопределённый владелец MediaAsset

Факт: MediaAsset используется Person, Group, Genre, Dance и Story, но domain overview помещал его среди данных Music Catalog, одновременно называя supporting capability.

Сценарий отказа: Music Catalog начинает владеть изображениями Dance и Story либо metadata прав дублируются по contexts.

Исправление: общий Media Management внутри монолита владеет MediaAsset metadata и storage identity; contexts ссылаются на MediaAssetId. Граница подтверждена пользователем 2026-08-15.

Уточнение после обсуждения: Media Management также владеет playback MediaReference и streaming provider adapters. В будущем storage, previews и provider integrations выделяются вместе в один Media Service; музыкальное аудио проект не хранит.

## Существенные несогласованности

### Неоднозначный MCP resource `artists`

Факт: модель разделяет Person/Performer и Group, но AI scope публиковал `music://artists/{id}`.

Риск: один ID namespace и contract снова смешивают человека и коллектив.

Исправление: resources разделены на `performers/{person_id}` и `groups/{id}`.

### Evidence было определено только как поддерживающее

Факт: `disputed` требует противоречащего материала, а Workshop 004 ввёл роли `supports`, `opposes`, `context`; glossary описывал Evidence только как поддержку.

Исправление: glossary синхронизирован с тремя ролями и условиями statuses.

### Публичные ссылки были только разрешимыми

Факт: Visitor не видит drafts, но aggregate policy требовала лишь существования reference.

Сценарий отказа: опубликованная Story или Recording содержит обязательную ссылку на draft и формирует недоступную страницу.

Исправление: обязательная reference при публикации должна быть доступна целевой публичной аудитории.

### Границы packages не фиксируются против подготовки к выделению

Факт: supporting capabilities не должны создавать пустые modules, но новая цель требует держать сильных кандидатов на краю.

Разрешение: логические seams и dependency direction фиксируются сейчас; конкретный package создаётся только первой использующей story. Пустой scaffolding по-прежнему запрещён.

## Проверенные непротиворечивые решения

- один deployment unit сейчас совместим с отдельным worker позднее: это разные этапы;
- отсутствие event bus в MVP совместимо с будущей task queue: task и event имеют разную семантику;
- одна реляционная БД совместима с S3-compatible storage: БД владеет metadata, object storage — bytes;
- отсутствие отдельной vector DB совместимо с RAG MVP: vector index производен и выбирается на этапе реализации;
- отсутствие Media bounded context совместимо с Media Management как supporting capability;
- малые aggregates совместимы с большим графом чтения: Discovery собирает read models без расширения write transaction;
- DDD context не обязан соответствовать service.
- объединение storage/previews и streaming adapters в Media не конфликтует с Music Catalog: Music владеет Recording, Media — только binary assets и внешние способы воспроизведения.

## Допустимые риски и проверки

| Риск | Проверка перед реализацией |
|---|---|
| слишком много ports | у каждого port есть внешняя/заменяемая граница или утверждённый process candidate |
| скрытая связность через ORM | architecture test запрещает импорт persistence models другого module |
| потеря идемпотентности AI jobs | повтор job/proposal ID не создаёт второй доменный объект |
| рассинхронизация производного index | index полностью перестраивается из SourceFragment/опубликованных данных |
| недоступная public reference | contract/integration test публикации проверяет visibility обязательных targets |
| media orphan после частичного отказа | повторяемый finalize/cleanup workflow и аудит storage key |

## Оставшиеся решения, не являющиеся противоречиями

- ADR-0002, ADR-0003, Media Management и целевая группировка сервисов приняты пользователем 2026-08-15;
- конкретные storage, vector, search и queue technologies остаются осознанными non-decisions до соответствующей story/ADR;
- продуктовые вопросы регистрации, editor self-publish, стартового корпуса и прав хранения источников остаются открытыми и не подменяются архитектурными решениями.

## Рекомендация devil's advocate

Не принимать вариант «порт для каждого модуля» и не выделять сервисы заранее. Использовать принятый extraction-ready monolith только для ранжированных кандидатов. Перед реализацией каждого port проверить реальную границу подмены; перед отдельным process провести failure-mode и idempotency workshop.
