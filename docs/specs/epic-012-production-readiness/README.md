# EPIC-012: Production readiness

Статус: `draft`.

Tracker: [GitHub issue #8](https://github.com/K-Mickey/roots-of-rhythm/issues/8), future backlog.

## Цель

Владелец проекта может безопасно открыть сервис для публичного трафика, обнаруживать эксплуатационные проблемы и восстанавливать работоспособность без догадок.

Это enabling epic с проверяемым пользовательским результатом для роли Owner/Operator. Он не является контейнером для любой инфраструктуры: в него входит только то, что непосредственно обеспечивает безопасную и наблюдаемую публичную эксплуатацию.

## Ценность

- публичные сценарии не остаются без базовой защиты от abuse и распространённых атак;
- проблемы обнаруживаются раньше случайной жалобы пользователя;
- alert содержит достаточно контекста для реакции;
- deployment, migration, backup и rollback имеют проверяемый путь;
- меры вводятся соразмерно риску, без преждевременного Kubernetes и собственного observability cluster.

## Граница по этапам

EPIC не блокирует scaffolding и локальную реализацию STORY-001.

До обязательного pull request workflow нужны:

- воспроизводимые lock, format, lint, type, test, contract и build checks;
- проверка утечек секретов;
- coverage нового кода и SonarQube Cloud quality gate.

До staging нужны:

- structured logs, correlation/request ID и release/environment labels;
- error tracking;
- базовый внешний uptime check.

До первого публичного трафика нужны:

- HTTPS и Caddy configuration;
- firewall/trusted-proxy/request-size/time limits и закрытый PostgreSQL;
- внешний edge для DDoS/WAF там, где это подтверждено deployment ADR;
- защита login и других дорогих endpoints от brute force/abuse;
- лимиты по IP и/или authenticated account там, где определён субъект и стоимость операции;
- OpenTelemetry telemetry, минимальные dashboards и Telegram/email alerts;
- backup/restore verification, migration и rollback runbooks.

Точные thresholds не задаются до появления endpoint cost model и baseline. Rate limit должен различать сетевую атаку, анонимный abuse, злоупотребление authenticated account и легитимную высокую активность.

## Независимые work items

### OPS-001: защита edge, запросов и аккаунтов

Результат: публичный deployment имеет эшелонированную защиту, а дорогие или чувствительные операции ограничиваются по подходящему субъекту.

Включает:

- Caddy как origin reverse proxy;
- внешний DDoS/WAF edge перед origin;
- ограничения body/header/time и trusted proxies;
- brute-force protection;
- endpoint-specific rate limits;
- authenticated account quotas/rate limits при появлении соответствующего сценария;
- security verification и runbook изменения/отключения лимитов при false positives.

### OPS-002: observability и оповещения

Результат: ошибки, недоступность и деградация ключевых сценариев обнаруживаются автоматически.

Включает:

- error tracking;
- OpenTelemetry traces/metrics/log correlation;
- Grafana Cloud или принятый ADR-аналог;
- внешний uptime check;
- Telegram как основной и email как резервный contact point;
- минимальные service, PostgreSQL и host dashboards;
- правила redaction, sampling, retention и actionable alert format.

### OPS-003: безопасная поставка и восстановление

Результат: release можно развернуть, откатить и восстановить с проверяемым сохранением данных.

Включает migrations, application rollback, automated off-host backups, restore drill и эксплуатационные runbooks.

### OPS-004: CI quality gate

Статус: `accepted`. Подробная спецификация: [CI quality gate](ci-quality-gate.md).

Результат: pull request получает воспроизводимые required checks качества, тестов, собираемости, секретов и Sonar Way до merge; CodeQL, Dependency Review и E2E дают отдельный сигнал без расписания.

OPS-004 не включает deployment, Sentry или telemetry и может выполняться независимо от остальных work items EPIC-012.

## Вне epic

- Kubernetes без отдельного доказанного требования;
- собственный Prometheus/Loki/Tempo/Grafana cluster только ради наличия технологий;
- защита от гипотетических атак без threat model;
- Redis/queue/cache без отдельного use case;
- SLA, которое проект не готов измерять и поддерживать.

## Зависимости и решения

- [ADR-0004: application stack](../../decisions/0004-application-stack.md)
- [Operations research](../../research/development-deployment-operations-stack.md)
- [OPS-004: CI quality gate](ci-quality-gate.md)
- отдельный deployment/security/observability ADR перед реализацией обязательных production work items.

## Открытые вопросы

- конкретный VPS/managed PostgreSQL/edge provider выбирается перед deployment с учётом региона, оплаты и бюджета;
- thresholds и account quotas определяются после появления защищаемых endpoints и baseline;
- retention и sampling telemetry уточняются до staging.
