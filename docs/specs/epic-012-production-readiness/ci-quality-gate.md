# OPS-004: CI quality gate

Статус: `accepted`.

Родитель: [EPIC-012](README.md).

## Цель

Каждое изменение получает воспроизводимую автоматическую проверку качества, безопасности и собираемости до merge.

CI не выполняет deployment и не получает production credentials. Логирование, Sentry, OpenTelemetry, backup и rollback остаются отдельными work items EPIC-012.

## Функциональные требования

- `CI-FR-001`: pull request в `main`, push в `main` и ручной запуск выполняют основной CI без scheduled triggers.
- `CI-FR-002`: required jobs проверяют lockfiles, format, lint, types, unit/integration tests, OpenAPI drift, production build и утечки секретов.
- `CI-FR-003`: backend и frontend создают coverage reports, которые импортирует один SonarQube Cloud project.
- `CI-FR-004`: Sonar Way блокирует новое покрытие ниже 80%, новые reliability/security issues, непросмотренные hotspots и duplication нового кода выше 3%.
- `CI-FR-005`: CodeQL `security-extended` и Dependency Review дают отдельный PR-сигнал; сначала они не входят в required branch protection.
- `CI-FR-006`: Playwright smoke запускается после push в `main` или вручную и сохраняет диагностику при ошибке.
- `CI-FR-007`: корневой README даёт краткий вход в продукт, локальный запуск, проверки и подробную документацию.

## Нефункциональные требования

- `CI-NFR-001`: workflow permissions минимальны; сторонние actions закреплены полным commit SHA.
- `CI-NFR-002`: зависимости устанавливаются из lockfiles, package-manager caches не содержат secrets, `.venv` или `node_modules`.
- `CI-NFR-003`: один ref имеет не более одного актуального CI-run; устаревший run отменяется.
- `CI-NFR-004`: fork pull request выполняет проверки без доступа к `SONAR_TOKEN`; отсутствие token не раскрывает и не подменяет secret.
- `CI-NFR-005`: CI-команды используют те же Make targets, что локальная разработка.

## Required quality gate

| Job | Проверяет |
| --- | --- |
| `quality` | lockfiles, Ruff, ESLint, Prettier, mypy, TypeScript и OpenAPI drift |
| `tests` | PostgreSQL migrations, backend unit/integration, frontend component tests и coverage |
| `build` | production backend/frontend images |
| `gitleaks` | hardcoded tokens, keys и passwords |
| `sonar` | Sonar Way quality gate и импорт coverage |

CodeQL, Dependency Review и E2E остаются видимыми checks, но становятся required только после нескольких стабильных прогонов и отдельного решения. E2E не входит в pull request workflow.

## Acceptance criteria

1. Given чистый checkout, when выполняются documented setup и Make targets, then lock checks, coverage tests и build завершаются воспроизводимо.
2. Given stale lockfile, format/type/test/contract/build error или секрет, when запускается CI, then соответствующий required job завершается ошибкой.
3. Given Python и TypeScript tests, when завершается `tests`, then Sonar получает Cobertura XML и LCOV по стабильным путям.
4. Given красный Sonar Way gate, when анализ завершается, then job `sonar` блокирует merge.
5. Given fork PR без repository secrets, when запускается CI, then общие проверки работают, Sonar scan пропускается без раскрытия token.
6. Given E2E failure, when smoke завершается, then доступны Playwright artifacts и Compose logs, а ephemeral stack остановлен.
7. Given repository configuration, then ни один workflow не содержит `schedule`.

## Вне scope

- Semgrep вместе с Sonar и CodeQL без project-specific правил;
- blocking `pip-audit` / `pnpm audit`, Hadolint, actionlint и отдельный markdown link checker;
- Dependabot schedules, pre-commit framework и self-hosted runners;
- deployment, production secrets, Sentry и telemetry.

## Внешняя настройка после первого зелёного run

1. Импортировать публичный repository в SonarQube Cloud и сверить organization/project keys.
2. Добавить `SONAR_TOKEN` в GitHub Actions secrets.
3. Включить Dependency Graph, Secret Scanning и Push Protection.
4. Защитить `main` required checks: `quality`, `tests`, `build`, `gitleaks`, `sonar`.
