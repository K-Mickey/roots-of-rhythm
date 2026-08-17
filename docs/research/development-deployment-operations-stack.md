# Development, deployment и operations stack

Статус: `research — recommendations, not an accepted ADR`.

Дата проверки: 2026-08-17.

Цель: показать минимальный сопутствующий набор для стека из [ADR-0004](../decisions/0004-application-stack.md), не добавляя production infrastructure до её сценария.

## Локальная разработка

Рекомендуется:

- backend и frontend запускать на host для быстрого hot reload;
- PostgreSQL запускать в Docker Compose;
- root `Makefile` даёт единые `setup`, `dev`, `lint`, `typecheck`, `test`, `contract`, `build`;
- `.env.example` содержит только имена и безопасные примеры, не секреты;
- full-container local profile добавляется для CI/parity, а не как единственный способ писать код.

## CI quality gate

Для каждого change:

1. OpenAPI lint и generated-client drift check.
2. Backend Ruff, mypy, unit и PostgreSQL integration tests.
3. Frontend ESLint, formatting, TypeScript, Vitest/component tests.
4. Production builds backend image и Next.js.
5. Playwright smoke test для critical public scenario.
6. Dependency/security scanning после появления lockfiles и images.

Первый кандидат CI — GitHub Actions, если repository размещается на GitHub. Конкретный CI provider не фиксируется до выбора repository hosting.

## Deployment-варианты

### A. Один VPS + Docker Compose + Caddy

Состав:

- Caddy завершает TLS и маршрутизирует `/api/*` в Litestar, остальное в Next.js;
- backend и frontend имеют разные containers, но один release version;
- PostgreSQL либо управляется provider, либо запущен на VPS с обязательными off-host backups и restore drills.

Плюсы: недорого, прозрачно, полезно для изучения operations, нет platform lock-in.  
Минусы: OS patching, backups, alerts, capacity и rollback — ответственность проекта.

Caddy автоматизирует HTTPS/certificate renewal и поддерживает reverse proxy с health checks: [automatic HTTPS](https://caddyserver.com/docs/automatic-https), [reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

### B. PaaS для frontend/backend + managed PostgreSQL

Плюсы: меньше operations, быстрее first public release, обычно есть managed TLS, logs и rollbacks.  
Минусы: дороже по мере роста, platform-specific limits, возможные separate origins и сложнее cookie auth.

Конкретный provider нужно выбирать перед первым public deployment по бюджету, региону, payment availability, backups и data residency. Этот research не выбирает provider заранее.

PaaS был указан как альтернатива не из-за требования архитектуры, а потому что он снимает с одного разработчика часть эксплуатации: TLS, rollout, restart, logs, rollback и иногда backups/managed database. Для учебной цели освоить deployment и прозрачнее понимать систему предпочтительный кандидат — VPS + Compose + Caddy; PaaS остаётся запасным путём к быстрому публичному релизу.

### C. Kubernetes

Не рекомендуется. Нет ни independent services/teams, ни autoscaling/SLA requirement, которые оправдывают cluster lifecycle, ingress, secrets, upgrades и observability stack.

## Production baseline до публичного релиза

Обязательно:

- same-origin HTTPS;
- readiness/liveness endpoints без секретов и диагностических утечек;
- structured logs, request ID и correlation между proxy, Next.js и Litestar;
- error tracking до публичного трафика;
- применение migrations как отдельный one-shot deployment step, а не параллельно каждым app replica;
- automated database backups, retention, encryption и проверенное восстановление;
- secrets только из deployment environment/secret store;
- resource limits, restart policy и disk-space monitoring;
- понятный rollback application images; database rollback не подменяется destructive down migration.

## Edge security: Caddy, Nginx и DDoS

Caddy и Nginx на origin решают TLS termination, reverse proxy, request limits и часть abuse protection, но не являются полной DDoS-защитой. Если поток уже заполнил сетевой канал VPS, приложение и локальный proxy не могут его освободить.

Рекомендуемая цепочка публичного трафика:

```text
Internet
  -> внешний edge: DNS/CDN, L3/L4/L7 DDoS mitigation, WAF/rate limits
  -> Caddy на VPS: TLS, routing, body/header/time limits, trusted proxy policy
  -> Litestar: authentication, authorization, validation, endpoint-specific limits
  -> PostgreSQL
```

- Caddy выбирается за простой configuration и автоматический HTTPS. Rate limiting не входит в стандартные Caddyfile directives; отображаемые в каталоге rate-limit modules являются non-standard plugins и требуют custom build, что для стартового проекта не оправдано: [стандартные directives](https://caddyserver.com/docs/caddyfile/directives), [каталог modules](https://caddyserver.com/docs/modules/http.handlers.rate_limit).
- Nginx имеет зрелые built-in `limit_req`/`limit_conn` controls и оправдан, если origin-level traffic shaping станет самостоятельным требованием: [Nginx connection limiting](https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html).
- Внешний edge нужен именно для volumetric attacks и управляемого WAF. Например, Cloudflare выполняет mitigation на своей сети до origin и отдельно поддерживает rate-limiting rules: [DDoS protection](https://developers.cloudflare.com/ddos-protection/), [rate limiting](https://developers.cloudflare.com/waf/rate-limiting-rules/).
- Litestar RateLimitMiddleware применим для дорогих application endpoints и brute-force/abuse policy, но не заменяет edge; при работе за proxy нельзя доверять forwarded headers от произвольного клиента: [Litestar middleware](https://docs.litestar.dev/latest/usage/middleware/builtin-middleware.html).

До публичного релиза также нужны firewall с открытыми только необходимыми портами, SSH keys, security updates, ограничения размера и времени запросов, корректный trusted-proxy allowlist, non-root containers где практично и отсутствие прямого публичного доступа к PostgreSQL.

## Observability и информирование

Необходимо разделять два класса инструментов:

| Вопрос | Инструмент | Стартовое решение |
|---|---|---|
| Какое исключение сломало запрос, в каком release и у каких пользователей? | error tracking | Sentry; Rollbar допустимая замена |
| Почему запрос медленный, где прошло время, что происходит с PostgreSQL/host? | metrics, logs, traces | OpenTelemetry -> Grafana Cloud |
| Доступен ли сайт снаружи? | uptime probe | внешний HTTP check |
| Куда отправлять alert? | alert routing | Telegram для быстрого сигнала + email как резерв |

Sentry предлагается раньше Rollbar из-за единого зрелого пути для Python/ASGI и Next.js и большей вероятности найти готовые integration recipes: [Sentry ASGI](https://docs.sentry.io/platforms/python/integrations/asgi/), [Sentry Next.js](https://docs.sentry.io/platforms/javascript/guides/nextjs/). Framework-specific package наподобие `django-rollbar` не требуется: Litestar — ASGI application, интеграция ставится на ASGI/Python boundary. Rollbar остаётся технически корректной альтернативой и официально поддерживает Next.js App Router: [Rollbar Next.js](https://docs.rollbar.com/docs/nextjs).

Grafana Cloud предлагается как managed backend, чтобы сначала изучить сигналы и dashboards, не обслуживать Prometheus/Loki/Tempo/Grafana как ещё один продукт. Litestar имеет OpenTelemetry plugin, а Grafana Cloud принимает metrics, logs и traces по OTLP: [Litestar OpenTelemetry](https://docs.litestar.dev/latest/usage/metrics/open-telemetry.html), [Grafana Cloud OTLP](https://grafana.com/docs/grafana-cloud/send-data/otlp/). Grafana Alerting поддерживает contact points, включая Telegram и email: [Grafana contact points](https://grafana.com/docs/grafana/latest/alerting/fundamentals/notifications/contact-points/).

Этапность:

1. Первая vertical slice: structured JSON logs, request/correlation ID, release/environment labels; локальное логирование SQL без значений чувствительных параметров.
2. Перед staging/public traffic: error tracking, внешний uptime check, OpenTelemetry traces для Next.js -> Litestar -> SQLAlchemy, минимальные service/DB/host dashboards и Telegram/email alerts.
3. После появления фоновых работ: отдельные job metrics, retries, queue depth и dead-letter alerts.
4. Self-hosted Grafana stack — только ради явной учебной цели, требований к данным или измеренно выгодной стоимости.

Не отправлять в telemetry access tokens, cookies, пароли, полные search prompts с персональными данными и необработанные SQL bind values. Alert должен быть actionable: содержать environment, service, symptom, threshold, dashboard/runbook link и не дублировать каждую ошибку отдельным сообщением.

## Контроль качества PostgreSQL-запросов

Качество запроса не сводится к одному порогу времени: важны частота, суммарная стоимость, tail latency, возвращаемые строки, I/O, блокировки и корректность плана на реалистичном объёме данных.

Минимальный набор:

- `pg_stat_statements` агрегирует planning/execution statistics нормализованных запросов; отслеживать `calls`, total/mean execution time, rows, shared/temp block I/O и долю запроса в общей DB load: [PostgreSQL pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html);
- `EXPLAIN (ANALYZE, BUFFERS)` применяется к конкретным медленным critical queries на staging-like data; `ANALYZE` действительно исполняет запрос, поэтому write statement запускать только в откатываемой транзакции или на безопасной копии: [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html);
- OpenTelemetry/SQLAlchemy spans связывают endpoint latency с SQL, не логируя параметры;
- PostgreSQL/system metrics показывают connections/pool saturation, long transactions, locks, deadlocks, cache/read I/O, disk и replication/backup health, если они появятся;
- для ключевых read models возможны integration regression checks на число SQL statements, чтобы ловить N+1; такие проверки добавляются вместе с реализацией после отдельного разрешения на изменение tests.

Не фиксировать сейчас универсальное правило «каждый запрос быстрее 100 ms». Сначала собрать baseline на seed и затем на реалистичном наборе. SLO задавать пользовательскому endpoint (например, p95 Genre page API), а SQL budgets — только известным critical queries. Медленный редкий editorial query и частый публичный query имеют разную цену.

## Управление задачами и процессом

Принятый старт — GitHub Issues + GitHub Projects + Milestones. Это держит specification, issue, pull request и CI рядом; отдельный Linear/Jira пока не создаёт дополнительной ценности. GitHub Projects поддерживает table/board/roadmap views, custom fields, charts и automation: [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects). Точный процесс и pre-code gate зафиксированы в [delivery workflow](../roadmap/delivery-workflow.md).

Источники и уровни детализации:

```text
docs/specs Epic/Story (почему, поведение, acceptance criteria)
  -> GitHub Issue (поставляемая задача или небольшой технический шаг)
  -> Pull Request (реализация, проверки, ссылка на issue/spec)
  -> Project/Milestone (состояние и граница релиза)
```

Минимальная доска: `Backlog -> Ready -> In progress -> Review -> Done`, плюс флаг `Blocked`. Поля: Epic/Story, priority, type и milestone; estimates/iterations добавляются только если они помогают планированию. Для solo-разработки WIP limit — одна основная задача в `In progress`.

Контролировать процесс лучше не количеством story points и commits, а:

- cycle time от `In progress` до `Done`;
- возраст заблокированных задач;
- доля незапланированной работы/дефектов;
- escaped defects после merge/release;
- изменение scope уже утверждённой story;
- прохождение acceptance criteria и CI quality gate.

Linear имеет смысл рассмотреть при росте команды или когда GitHub Projects перестанет удобно поддерживать triage/roadmap. Документы SDD остаются источником истины требований; tracker показывает работу и не заменяет specification.

## Добавлять по триггеру, а не сразу

| Технология | Триггер |
|---|---|
| S3-compatible storage | появились управляемые images/files и backup policy |
| Worker + queue | image/RAG job не вписывается в request, нужны retries/backpressure |
| Redis | есть конкретный shared cache/rate-limit/session use case |
| OpenTelemetry/Grafana Cloud | перед staging/public traffic нужны latency, traces, DB/host metrics и alerts |
| Search engine | PostgreSQL search измеренно не выполняет relevance/latency requirements |
| Vector extension/database | появились RAG corpus, retrieval evaluation и измерения |
| Kubernetes | несколько independent services/teams и реальная cluster requirement |

## Рекомендация

1. Сейчас утвердить application stack, а не cloud provider.
2. Для development добавить только PostgreSQL в Compose и quality toolchain.
3. Предварительно предпочесть VPS + Docker Compose + Caddy для прозрачности и обучения; перед public release проверить текущего provider, edge DDoS/WAF и managed PostgreSQL по бюджету/региону.
4. До staging подготовить error tracking; до public traffic — OpenTelemetry/Grafana Cloud, uptime и Telegram/email alerts.
5. Использовать GitHub Issues/Projects/Milestones как проекцию SDD-работы, не как замену спецификациям.
6. Включить `pg_stat_statements` и строить performance budgets от измерений critical read models.
7. Не добавлять Kubernetes, Redis, queue, S3, search и vector infrastructure в STORY-001.
