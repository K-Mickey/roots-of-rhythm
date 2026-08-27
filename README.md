# Roots of Rhythm

[![CI](https://github.com/K-Mickey/roots-of-rhythm/actions/workflows/ci.yml/badge.svg)](https://github.com/K-Mickey/roots-of-rhythm/actions/workflows/ci.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=K-Mickey_roots-of-rhythm&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=K-Mickey_roots-of-rhythm)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=K-Mickey_roots-of-rhythm&metric=coverage)](https://sonarcloud.io/summary/new_code?id=K-Mickey_roots-of-rhythm)

Roots of Rhythm — исследовательский сервис об истории музыкальных жанров, исполнителей, произведений, записей и связей между ними. Проект развивается по Spec-Driven Development: спецификации определяют поведение, код реализует его, проверки подтверждают соответствие.

## Стек

- Python 3.14, Litestar, SQLAlchemy и PostgreSQL 18;
- TypeScript, Next.js, React и Mantine;
- uv, pnpm, Docker Compose и GitHub Actions.

## Быстрый старт

Нужны `uv` 0.12+, Node.js 24, pnpm 11.24 и Docker Desktop.

```bash
make setup
make db-up
make migrate
make seed
```

Для разработки:

```bash
make backend-dev
make frontend-dev
```

Полный production-like stack: `make up`; остановка без удаления данных: `make down`.

## Проверки

```bash
make lock-check
make check
make test-integration
make test-coverage
make test-e2e
```

`make test-coverage` создаёт `backend/coverage.xml` и `frontend/coverage/lcov.info` для SonarQube Cloud.

## Структура

```text
backend/   Litestar application, migrations и backend tests
frontend/  Next.js application, component tests и Playwright smoke
docs/      product, domain, architecture, specifications и API contract
```

## Документация

- [Навигация по документации](docs/README.md)
- [Архитектура](docs/architecture.md)
- [Разработка и проверки](docs/development.md)
- [Спецификации](docs/specs/README.md)
- [OpenAPI-контракт](docs/api/README.md)
