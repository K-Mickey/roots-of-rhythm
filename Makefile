SHELL := /bin/sh

.PHONY: help setup lock db-up test-db-setup up down ps logs backend-dev frontend-dev migrate seed \
	format format-check lint typecheck test-unit test-integration test-e2e contract-check build check

POSTGRES_USER ?= roots
DATABASE_URL ?= postgresql+psycopg://roots:roots@127.0.0.1:5432/roots_of_rhythm
TEST_POSTGRES_DB ?= roots_of_rhythm_test
TEST_DATABASE_URL ?= postgresql+psycopg://roots:roots@127.0.0.1:5432/$(TEST_POSTGRES_DB)
PNPM_VERSION := 11.19.0
PNPM := $(shell \
	if command -v pnpm >/dev/null 2>&1; then command -v pnpm; \
	elif command -v corepack >/dev/null 2>&1; then echo "corepack pnpm"; \
	else echo "npx --yes pnpm@$(PNPM_VERSION)"; fi)

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install locked backend and frontend dependencies
	cd backend && uv sync --frozen
	$(PNPM) --dir frontend install --frozen-lockfile

lock: ## Refresh dependency lockfiles from manifests
	cd backend && uv lock
	$(PNPM) --dir frontend install --lockfile-only

db-up: ## Start PostgreSQL and wait until it is ready
	docker compose up -d --wait postgres

test-db-setup: db-up ## Create the isolated integration database if absent and migrate it
	docker compose exec -T postgres psql -U $(POSTGRES_USER) -d postgres -tAc \
		"SELECT 1 FROM pg_database WHERE datname = '$(TEST_POSTGRES_DB)'" | grep -q 1 \
		|| docker compose exec -T postgres createdb -U $(POSTGRES_USER) $(TEST_POSTGRES_DB)
	cd backend && DATABASE_URL=$(TEST_DATABASE_URL) uv run alembic upgrade head

up: ## Build and start the complete local stack
	docker compose up -d --build --wait

down: ## Stop the stack while preserving the PostgreSQL volume
	docker compose down

ps: ## Show Compose service state
	docker compose ps

logs: ## Follow Compose logs
	docker compose logs -f

backend-dev: ## Run Litestar with reload on the host
	cd backend && DATABASE_URL=$(DATABASE_URL) PYTHONPATH=src uv run roots-of-rhythm api --host 127.0.0.1 --port 8000 --reload

frontend-dev: ## Run Next.js development server on the host
	$(PNPM) --dir frontend dev

migrate: ## Apply backend migrations to the local database
	cd backend && DATABASE_URL=$(DATABASE_URL) uv run alembic upgrade head

seed: ## Load controlled Genre and Performer corpus (idempotent)
	cd backend && DATABASE_URL=$(DATABASE_URL) PYTHONPATH=src uv run roots-of-rhythm seed

format: ## Format backend and frontend sources
	cd backend && uv run ruff format . && uv run ruff check . --fix
	$(PNPM) --dir frontend format

format-check: ## Check formatting without modifying files
	cd backend && uv run ruff format --check .
	$(PNPM) --dir frontend format:check

lint: ## Run backend and frontend linters
	cd backend && uv run ruff check .
	$(PNPM) --dir frontend lint

typecheck: ## Run Python and TypeScript type checks
	cd backend && uv run mypy
	$(PNPM) --dir frontend typecheck

test-unit: ## Run backend and frontend unit tests
	cd backend && uv run pytest -m "not integration"
	$(PNPM) --dir frontend test

test-integration: test-db-setup ## Run PostgreSQL integration tests against the isolated database
	cd backend && TEST_DATABASE_URL=$(TEST_DATABASE_URL) uv run pytest -m integration

test-e2e: ## Run Playwright smoke tests against a running stack
	$(PNPM) --dir frontend test:e2e

contract-check: ## Lint OpenAPI and verify generated TypeScript types
	$(PNPM) --dir frontend api:lint
	$(PNPM) --dir frontend api:check

build: ## Build production backend and frontend images
	docker compose build

check: format-check lint typecheck test-unit contract-check build ## Run the local quality baseline
