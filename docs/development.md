# Разработка

Статус: `active`.

## Предварительные требования

- `uv` 0.11+ и доступный CPython 3.14;
- Node.js 24 LTS и `pnpm` 11.19 (если `pnpm` нет в PATH, Makefile берёт Corepack или `npx --yes pnpm@11.19.0`);
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
| `make seed` | корень | PostgreSQL, миграции | Идемпотентно загружает controlled Genre corpus (Jazz, Swing, Jump Blues и две published relations). |

Локальные значения окружения перечислены в `.env.example`. Compose публикует порты только на `127.0.0.1`: PostgreSQL `5432`, backend `8000`, frontend `3000`. Frontend SSR читает `API_BASE_URL` (host default `http://127.0.0.1:8000`, в Compose — `http://backend:8000`).

Публичная главная: `http://127.0.0.1:3000/`. Каталог жанров: `http://127.0.0.1:3000/genres`. Публичная Genre page: `http://127.0.0.1:3000/genres/{genre_id}`. Seed Swing: `/genres/01a0147a-8508-74b7-9689-e7c133e4e7a5`.

## Проверки

| Команда | Требования | Результат |
| --- | --- | --- |
| `make format` | `make setup` | Форматирует Python и frontend-файлы. |
| `make format-check` | `make setup` | Проверяет Ruff formatter и Prettier без записи. |
| `make lint` | `make setup` | Запускает Ruff и ESLint. |
| `make typecheck` | `make setup` | Запускает mypy и TypeScript compiler. |
| `make test-unit` | `make setup` | Запускает backend unit tests и Vitest. |
| `make test-integration` | Docker, `make setup` | Поднимает PostgreSQL, применяет Alembic migrations и проверяет readiness и persistence с реальной БД. |
| `make test-e2e` | запущенный `make up` + `make seed`, Chromium | Playwright: `/`, identity/not-found HOME-0, header «Жанры», каталог `/genres`, seed Swing page и переходы relation-имён Swing→Jazz и Swing→Jump Blues. |
| `make contract-check` | `make setup` | Проверяет OpenAPI через Redocly и отсутствие drift в generated TypeScript contract. |
| `make build` | Docker | Собирает production images backend и frontend. |
| `make check` | Docker, `make setup` | Выполняет format-check, lint, typecheck, unit tests, contract-check и Docker build. |

Backend запускается только через Click CLI. Из `backend/` доступны `uv run roots-of-rhythm --help`, `uv run roots-of-rhythm api --help` и `uv run roots-of-rhythm seed`; Makefile и Docker используют ту же команду. Для host, port и reload значения Click options имеют приоритет над `API_HOST`, `API_PORT`, `API_RELOAD` из environment или `.env`; `DATABASE_URL` читается из тех же configuration sources без CLI override. Затем применяются локальные defaults. Конфигурация загружается при импорте `roots_of_rhythm.config` и остаётся неизменяемым snapshot на время жизни процесса.

## Health endpoints

- `GET http://127.0.0.1:8000/health/live` — процесс backend работает;
- `GET http://127.0.0.1:8000/health/ready` — backend может выполнить `SELECT 1` в PostgreSQL;
- `GET http://127.0.0.1:3000/api/health` — production frontend отвечает.
