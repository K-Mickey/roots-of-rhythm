# Разработка

Статус: `active`.

## Предварительные требования

- `uv` 0.11+ и доступный CPython 3.14;
- Node.js 24 LTS и `pnpm` 11.24 (если `pnpm` нет в PATH, Makefile берёт Corepack или `npx --yes pnpm@11.24.0`);
- Docker Desktop с Compose;
- Chromium для E2E: `cd frontend && pnpm exec playwright install chromium`.

Все команды ниже, кроме явно отмеченных, выполняются из корня репозитория.

## Установка и запуск

| Команда | Рабочая директория | Требования | Результат |
| --- | --- | --- | --- |
| `make setup` | корень | uv, pnpm | Устанавливает зависимости из `backend/uv.lock` и `frontend/pnpm-lock.yaml`. |
| `make db-up` | корень | Docker | Запускает PostgreSQL и ждёт readiness. |
| `make up` | корень | Docker | Собирает и запускает PostgreSQL, backend и production frontend с ожиданием readiness. |
| `make down` | корень | Docker | Останавливает stack, не удаляя named volume PostgreSQL. |
| `make backend-dev` | корень | PostgreSQL, `make setup` | Запускает Litestar на `127.0.0.1:8000` с hot reload. |
| `make frontend-dev` | корень | `make setup` | Запускает Next.js на `127.0.0.1:3000`. |
| `make migrate` | корень | PostgreSQL | Выполняет `alembic upgrade head`. |
| `make seed` | корень | PostgreSQL, миграции | Идемпотентно загружает controlled Genre/People/Group/Work corpus и три published Recording `Sixteen Tons` с facets, lyrics metadata, origin Claim и ListeningGuide. |

Локальные значения окружения перечислены в `.env.example`. Compose публикует порты только на `127.0.0.1`: PostgreSQL `5432`, backend `8000`, frontend `3000`. Frontend SSR читает `API_BASE_URL` (host default `http://127.0.0.1:8000`, в Compose — `http://backend:8000`).

Публичная главная: `http://127.0.0.1:3000/`. Каталоги: `/genres`, `/performers`, `/groups`, `/songs`, `/recordings`. Публичные страницы используют те же пути с `/{id}`. Seed Swing: `/genres/01a0147a-8508-74b7-9689-e7c133e4e7a5`; Louis Armstrong: `/performers/01a01a72-1be5-7542-b935-47f617f2cfd3`; Count Basie Orchestra: `/groups/01a01a72-2c01-7000-8000-000000000003`; Sixteen Tons: `/songs/01a01a72-3c01-7000-8000-000000000001`; Tennessee Ernie Ford Recording: `/recordings/01a01a72-4a01-7000-8000-000000000002`.

## Проверки

| Команда | Требования | Результат |
| --- | --- | --- |
| `make format` | `make setup` | Форматирует Python и frontend-файлы. |
| `make lock-check` | `make setup` | Проверяет согласованность manifests и lockfiles без обновления зависимостей. |
| `make format-check` | `make setup` | Проверяет Ruff formatter и Prettier без записи. |
| `make lint` | `make setup` | Запускает Ruff и ESLint. |
| `make typecheck` | `make setup` | Запускает mypy и TypeScript compiler. |
| `make test-unit` | `make setup` | Запускает backend unit tests и Vitest. |
| `make test-db-setup` | Docker, `make setup` | Идемпотентно создаёт БД `roots_of_rhythm_test` через запущенный сервис `postgres` и применяет к ней Alembic migrations. |
| `make test-integration` | Docker, `make setup` | Выполняет `make test-db-setup` и проверяет readiness и persistence на изолированной БД `roots_of_rhythm_test`. |
| `make test-coverage` | Docker, `make setup` | Запускает backend unit/integration и frontend tests; создаёт `backend/coverage.xml` и `frontend/coverage/lcov.info`. |
| `make test-e2e` | запущенный `make up` + `make seed`, Chromium | Playwright: `/`, identity/not-found HOME-0, header «Жанры», «Исполнители» и «Группы», каталоги `/genres`, `/performers` и `/groups`, seed Swing page, seed Louis Armstrong page, seed Count Basie Orchestra page и переходы relation-имён Swing→Jazz и Swing→Jump Blues. |
| `make contract-check` | `make setup` | Проверяет OpenAPI через Redocly и отсутствие drift в generated TypeScript contract. |
| `make build` | Docker | Собирает production images backend и frontend. |
| `make check` | Docker, `make setup` | Выполняет format-check, lint, typecheck, unit tests, contract-check и Docker build. |

Coverage локально не имеет общего `fail-under`: Sonar Way проверяет покрытие нового кода и не заставляет одномоментно переписывать существующий baseline.

## Continuous Integration

GitHub Actions запускает required jobs `quality`, `tests`, `build`, `gitleaks` и `sonar` для pull request в `main`, push в `main` и вручную. CodeQL и Dependency Review дают отдельный advisory-сигнал. Playwright smoke запускается только после push в `main` или вручную, чтобы тяжёлый browser сценарий не задерживал pull request.

SonarQube Cloud читает `backend/coverage.xml` и `frontend/coverage/lcov.info`. Для scan нужен repository secret `SONAR_TOKEN`; fork pull request без доступа к secrets выполняет остальные проверки и безопасно пропускает Sonar step.

Решение и acceptance criteria: [OPS-004: CI quality gate](specs/epic-012-production-readiness/ci-quality-gate.md).

## Изоляция БД для integration tests

Integration tests работают только с отдельной БД `roots_of_rhythm_test` и никогда не касаются development-БД `roots_of_rhythm`:

- `make test-db-setup` создаёт `roots_of_rhythm_test`, если её нет, через `docker compose exec postgres` — поэтому setup работает и на уже инициализированном named volume, где `docker-entrypoint-initdb.d` больше не выполняется;
- migrations применяются к `TEST_DATABASE_URL` (`make migrate` по-прежнему относится только к development-БД);
- fixtures в `backend/tests/support/postgres.py` очищают corpus tables (`classification_assignments`, `persons`, `classification_concepts`, claims, sources) и читают `TEST_DATABASE_URL`. pytest-env задаёт default на `roots_of_rhythm_test` (`D:` — не перезаписывает уже заданную переменную).

Перезапуск `make test-db-setup` идемпотентен: существующая БД не пересоздаётся, `alembic upgrade head` завершается без изменений.

Тест `test_unit_of_work_rolls_back_and_unique_name_is_case_insensitive` намеренно проверяет unique constraint на уровне PostgreSQL, поэтому при зелёном прогоне в логах `docker compose logs postgres` ожидается запись:

```text
ERROR:  duplicate key value violates unique constraint "uq_classification_concepts_kind_canonical_name_ci"
DETAIL:  Key (kind, lower(canonical_name::text))=(genre, swing) already exists.
STATEMENT:  UPDATE classification_concepts SET canonical_name=$1::VARCHAR WHERE classification_concepts.id = $2::UUID
```

Эта запись ожидаема: application-слой преобразует нарушение в `UniqueConstraintViolation`. Ошибкой считается отсутствие соответствующего исключения в тесте, а не сама строка в логе PostgreSQL.

Backend запускается только через Click CLI. Из `backend/` доступны `uv run roots-of-rhythm --help`, `uv run roots-of-rhythm api --help` и `uv run roots-of-rhythm seed`; Makefile и Docker используют ту же команду. Для host, port и reload значения Click options имеют приоритет над `API_HOST`, `API_PORT`, `API_RELOAD` из environment или `.env`; `DATABASE_URL` читается из тех же configuration sources без CLI override. Затем применяются локальные defaults. Конфигурация загружается при импорте `roots_of_rhythm.config` и остаётся неизменяемым snapshot на время жизни процесса.

## Health endpoints

- `GET http://127.0.0.1:8000/health/live` — процесс backend работает;
- `GET http://127.0.0.1:8000/health/ready` — backend может выполнить `SELECT 1` в PostgreSQL;
- `GET http://127.0.0.1:3000/api/health` — production frontend отвечает.
