# ADR-0004: application stack первой вертикали

Статус: `accepted`.

Дата: 2026-08-17.

## Контекст

STORY-001 и её UI/OpenAPI contracts утверждены. Для первой vertical slice нужны:

- публичная content-heavy Genre page, читаемая без обязательного client-side JavaScript;
- contract-first REST API;
- PostgreSQL для связей, Claims, Evidence и будущего full-text/vector развития без дополнительной БД на старте;
- явные DDD/Clean Architecture boundaries, которые не заменяются framework models;
- практика с популярным React/TypeScript frontend stack;
- позднейшие Editorial UI, RAG, MCP, agents и streaming integrations;
- разумная сложность для одного разработчика.

Стек должен служить проекту, а не становиться альтернативной архитектурой. Transport DTO, ORM models и React components не являются domain model.

## Решение

### Backend

- Python в поддерживаемой стабильной версии, точная версия фиксируется lock/toolchain при scaffolding;
- Litestar как тонкий HTTP/ASGI entrypoint;
- msgspec для явных transport DTO, JSON serialization/deserialization и доменных entities/value objects;
- domain `msgspec.Struct` и transport `msgspec.Struct` являются разными типами: HTTP DTO не передаётся в domain и domain entity не сериализуется в HTTP напрямую;
- Uvicorn как ASGI server;
- Click как единая runtime CLI backend: HTTP API и будущие MCP/worker processes являются отдельными командами одной CLI, прямой параллельный способ запуска не поддерживается;
- `python-decouple` только для чтения application configuration с приоритетом CLI override, environment, `.env`, default; frozen `msgspec.Struct` создаёт единый неизменяемый snapshot настроек процесса; библиотека не используется для domain или transport models;
- async HTTP/database adapters и async application use cases, когда они выполняют I/O; domain rules остаются обычным чистым Python.

Python `async` здесь не противоречит «синхронным application-вызовам» ADR-0001: contexts вызывают друг друга in-process в рамках одного request/response flow, без event bus, message delivery и eventual consistency. `async/await` только не блокирует event loop во время I/O.

Litestar генерирует OpenAPI 3.1 и поддерживает `msgspec.Struct` в схемах и JSON responses: [Litestar OpenAPI](https://docs.litestar.dev/main/usage/openapi/index.html), [responses](https://docs.litestar.dev/main/usage/responses.html). Framework DI подаёт application use cases в handlers, но framework repositories, transport DTO и ORM integration не определяют application ports. Домен теперь зависит от малой библиотеки msgspec, но не от Litestar, HTTP schema или JSON naming rules.

### Persistence

- PostgreSQL как единственная transactional database;
- SQLAlchemy 2.x как persistence mapper в infrastructure layer;
- Alembic для версионируемых migrations;
- Psycopg 3 async dialect;
- repository и Unit of Work определяются application-owned ports; ORM session не выходит в transport и не передаётся между contexts.

SQLAlchemy поддерживает с Psycopg 3 и sync, и async engine под одним dialect: [SQLAlchemy PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).

### Frontend

- React + TypeScript;
- Next.js App Router;
- Server Components/server rendering по умолчанию для data loading, route orchestration и публичной initial response;
- Client-side state и effects только для реальной интерактивности; Mantine components размещаются в минимально разумных client boundaries, требуемых библиотекой;
- Mantine как основная React UI library и design system всего frontend: layout primitives, typography, forms, navigation, overlays, feedback и будущий Editorial UI сначала строятся её средствами;
- Mantine theme как единый источник colors, typography, spacing, radii, breakpoints и component defaults;
- CSS Modules только для предметной композиции или поведения, которое нельзя выразить Mantine API без ухудшения читаемости; собственные базовые controls и параллельная styling system не создаются;
- Tailwind одновременно не подключается, чтобы не поддерживать две design systems;
- generated TypeScript types из `docs/api/openapi.yaml` через `openapi-typescript`; transport — native `fetch` или тонкий typed client;
- без Redux, global client store и TanStack Query в STORY-001: server data загружается на server boundary Next.js.

App Router использует Server Components, Suspense и layouts: [Next.js App Router](https://nextjs.org/docs/app), [production guide](https://nextjs.org/docs/app/guides/production-checklist). Mantine совместим с App Router, но его components требуют `MantineProvider` и являются Client Components. Они могут быть server-rendered, однако увеличивают client boundary и hydration относительно чистых Server Components; этот trade-off принят ради цельной design system и снижения объёма самописного UI. Public content обязан сохранять semantic markup, читаемый initial HTML и корректную работу content-сценария без обязательной клиентской интерактивности: [Mantine Next.js guide](https://mantine.dev/guides/next/), [CSS Modules](https://mantine.dev/styles/css-modules/).

### Dependency management и quality baseline

- `uv` + committed `uv.lock` для Python;
- устанавливаемый pure-Python `src` package собирается официальным `uv_build`; Hatchling добавляется только при появлении неподдерживаемой build-задачи;
- `pnpm` + committed lockfile для frontend; JavaScript workspace не создаётся, пока frontend package один;
- Ruff для Python lint/format, mypy для static typing;
- ESLint + Prettier для TypeScript/React;
- pytest для domain/application/integration tests;
- Vitest + React Testing Library для frontend unit/component tests;
- Playwright для небольшого набора critical end-to-end scenarios;
- Redocly CLI или эквивалентный OpenAPI 3.1 linter фиксируется при scaffolding; два contract linters не нужны;
- root `Makefile` как тонкие именованные entrypoints, без бизнес-логики в shell.

`uv` даёт project environment и reproducible lockfile: [uv projects and lockfiles](https://docs.astral.sh/uv/concepts/projects/). Playwright остаётся e2e tool, а не заменяет более быстрые unit/integration tests: [Playwright documentation](https://playwright.dev/docs/intro).

## Runtime и толкование deployment unit

Next.js SSR и Litestar требуют два runtime processes. Это не создаёт два domain services:

- Next.js — presentation entrypoint, не владеет domain data и не ходит в PostgreSQL;
- Litestar — единственный backend modular monolith;
- frontend и backend версионируются в одном repository и выпускаются одним координируемым release;
- один origin маршрутизирует `/api/*` в Litestar, а остальное — в Next.js, что не вводит CORS и упрощает будущую cookie session;
- независимые deployment lifecycle и network API между domain contexts не вводятся.

Это уточняет ADR-0001: `one deployment unit` означает один версионируемый application release без независимых сервисов, а не обязательно один OS process.

## Рассмотренные альтернативы

### FastAPI + Next.js

Плюсы:

- самый большой объём обучающих материалов и сторонних примеров среди современных Python API frameworks;
- узнаваемый стек на рынке;
- простой старт для небольшого API.

Минусы:

- Pydantic тесно связан с основной transport-моделью framework, тогда как пользователь выбрал msgspec;
- для желаемой структуры приложения Litestar даёт более цельный набор DI, lifecycle, OpenAPI и observability extension points;
- популярность сама по себе не является достаточным основанием менять выбранный учебный стек.

FastAPI основан на OpenAPI, JSON Schema, Starlette и Pydantic: [FastAPI features](https://fastapi.tiangolo.com/features/).

### Django + Next.js

Плюсы:

- mature ORM, migrations, authentication, permissions и admin;
- много готовых решений для content applications;
- admin может ускорить первичное заполнение простых моделей.

Минусы:

- Django models/ORM естественно тянут архитектуру к Active Record и framework-owned boundaries;
- изолировать Django ORM только в infrastructure можно, но тогда теряется часть его главной продуктивности;
- Editorial workflow с Claims, Evidence, independent publication и visibility gates не сводится к generic CRUD.

Django прямо описывает admin как model-centric internal tool и советует custom views для process-centric interface: [Django admin documentation](https://docs.djangoproject.com/en/6.1/ref/contrib/admin/).

### Django templates/HTMX без React

Плюсы: один runtime, проще deployment, SSR и sessions в одном framework.

Минусы: не выполняет учебную цель освоить популярный React/TypeScript stack; будущая интерактивная карта всё равно потребует отдельного frontend-кода.

### Litestar + React/Vite SPA

Плюсы: проще frontend build и static hosting, меньше server-side React concepts.

Минусы: initial content зависит от JavaScript, хуже выполняет NFR-002 и требования content/SEO-проекта. SSR позже потребует смены rendering architecture.

## Почему предлагается Litestar + msgspec + Next.js

1. Litestar даёт явные controller/DI/lifecycle boundaries и не навязывает ORM/admin architecture.
2. msgspec даёт единый строгий механизм описания Python-структур в domain и transport при сохранении явного mapping между ними.
3. Next.js даёт популярный React/TypeScript stack и SSR для public content.
4. OpenAPI остаётся явной границей Python/TypeScript, а не дублируется вручную.
5. Стек совместим с будущими AI/MCP на Python и богатой интерактивностью на React.
6. Litestar, SQLAlchemy и React остаются на краях Clean Architecture; domain/application code можно тестировать без ASGI, React и PostgreSQL. msgspec — осознанное исключение из полной независимости domain от внешних библиотек.

## Последствия

Положительные:

- популярный и переносимый full-stack набор навыков;
- SSR и client interactivity в одной frontend architecture;
- контракт связывает Python и TypeScript без общей domain model;
- PostgreSQL покрывает MVP без графовой, vector и search БД.
- Mantine ускоряет создание согласованного public и Editorial UI и даёт одну систему темизации вместо набора самописных controls.

Отрицательные:

- два runtime processes и два dependency ecosystems;
- OpenAPI generation/check обязан предотвращать drift;
- SSR добавляет Next.js caching/rendering semantics;
- async SQLAlchemy требует дисциплины transaction/session ownership.
- Mantine расширяет client boundary Next.js и требует контролировать bundle/hydration и доступность публичного content без JavaScript.
- domain связан с API и lifecycle msgspec; его замена потребует миграции domain types;
- повторное использование одного Struct как domain entity и HTTP DTO запрещено, поэтому mapping остаётся явной ценой границ.

### Почему не оставили msgspec только в transport

Это сохранило бы domain на stdlib dataclasses/plain classes и сделало бы замену msgspec дешевле. Вариант был исходно принят, но Product Owner выбрал один строгий механизм и для domain objects. Риск transport leakage ограничен разными типами и явным mapping.

## Явно не входит в это решение

- authentication/session implementation;
- конкретный cloud/VPS provider;
- S3, Redis, task queue, Elasticsearch, graph database и vector database;
- TanStack Query, Redux и rich-text editor до появления сценария;
- observability backend/provider;
- независимые frontend/backend release cycles.

## План изменения

- Litestar, msgspec и SQLAlchemy можно заменить при сохранении application ports, domain tests и OpenAPI contract.
- Next.js можно заменить другим renderer, если public API и semantic UI contract сохранены.
- Смена PostgreSQL существенно дороже и потребует отдельного ADR и data migration plan.

## Связанные документы

- [ADR-0001](0001-modular-monolith-context-boundaries.md)
- [ADR-0002](0002-aggregate-and-transaction-boundaries.md)
- [ADR-0003](0003-extraction-ready-monolith.md)
- [STORY-001](../specs/epic-001-genre-exploration/story-001-view-published-genre/README.md)
- [OpenAPI 0.2.0](../api/openapi.yaml)
- [UI contract](../specs/epic-001-genre-exploration/story-001-view-published-genre/ui.md)
- [Структура модулей](../module-structure.md)

## История изменений

- 2026-08-17: Product Owner изменил первоначальное решение «msgspec только для transport DTO»: `msgspec.Struct` также используется для domain entities/value objects, но domain и transport types не объединяются.
- 2026-08-17: backend зафиксирован как устанавливаемый `uv_build` package; Click принят единственной runtime CLI, `python-decouple` — изолированным механизмом configuration.
