# Структура модулей и тестов

Статус: `accepted`

Документ фиксирует организационные границы кода без выбора языка, framework и окончательных имён source roots.

## Основной принцип

Каждый bounded context и supporting capability получает собственную верхнеуровневую подпапку. Тесты зеркалят эти границы. Это один repository, codebase и deployment unit; внутреннее взаимодействие остаётся прямым и не имитирует HTTP/RPC.

Концептуальная проекция:

```text
src/
├── people/
├── music/
├── dance/
├── historical_knowledge/
├── editorial/
├── discovery/
├── media/
├── ai_research/
└── entrypoints/
    ├── web_or_api/
    └── mcp/

tests/
├── people/
├── music/
├── dance/
├── historical_knowledge/
├── editorial/
├── discovery/
├── media/
├── ai_research/
├── entrypoints/
└── architecture/
```

`src` и конкретные названия адаптируются к выбранному стеку, но соответствие «модуль → отдельная подпапка → зеркальные тесты» сохраняется.

## Внутренняя структура модуля

Создавать подпапку только когда в ней появляется реальный код:

```text
<module>/
├── domain/          # entities, value objects, policies
├── application/     # use cases, orchestration, owned ports
├── infrastructure/  # DB, SDK, filesystem and network adapters
└── presentation/    # только принадлежащий модулю transport mapping, если нужен
```

Не создавать четыре пустых слоя для простого модуля. Dependency direction важнее одинакового дерева директорий.

## Правила зависимостей

1. Domain не импортирует application, infrastructure, ORM, HTTP или SDK.
2. Application зависит от domain и определяет необходимые внешние ports.
3. Infrastructure реализует ports и может зависеть от framework/SDK.
4. Один модуль не импортирует ORM models, repositories или infrastructure другого.
5. Межмодульный вызов использует публичный application/query contract и стабильные IDs.
6. Media и AI Research не используют общую ORM session для изменения данных Core.
7. Entrypoint преобразует transport DTO и вызывает use case; доменные правила в transport не дублируются.
8. Общая папка `shared` не создаётся заранее. Код переносится туда только при нескольких реальных потребителях и отсутствии предметного владельца.

## Структура тестов

В папке каждого модуля находятся его unit и module-integration tests. Тесты внешних adapters остаются рядом с тестами владеющего модуля.

Отдельно:

- `tests/architecture` проверяет запрещённые imports и направление зависимостей;
- contract tests проверяют публичные application/port contracts на стороне владельца;
- end-to-end tests могут охватывать несколько модулей, но не заменяют локальные проверки;
- тестовые fixtures не становятся общим изменяемым доменным состоянием между модулями.

Точная test framework и команды определяются после выбора стека. Создание структуры не отменяет проектное правило: существующие тесты не изменяются без явного подтверждения пользователя.

## Будущее выделение

При запуске Media или AI Knowledge в отдельном process сначала переиспользуются их module/application boundaries и тесты. Сетевой contract, deployment и delivery tests добавляются только на этапе фактического выделения; заранее HTTP не имитируется.

Решение принято пользователем 2026-08-15.
