SHELL := /bin/sh

.PHONY: help setup lock db-up up down ps logs backend-dev frontend-dev migrate seed \
	format format-check lint typecheck test-unit test-integration test-e2e contract-check build check

DATABASE_URL ?= postgresql+psycopg://roots:roots@127.0.0.1:5432/roots_of_rhythm

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install locked backend and frontend dependencies
	cd backend && uv sync --frozen
	pnpm --dir frontend install --frozen-lockfile

lock: ## Refresh dependency lockfiles from manifests
	cd backend && uv lock
	pnpm --dir frontend install --lockfile-only

db-up: ## Start PostgreSQL and wait until it is ready
	docker compose up -d --wait postgres

up: ## Build and start the complete local stack
	docker compose up -d --build --wait

down: ## Stop the stack while preserving the PostgreSQL volume
	docker compose down

ps: ## Show Compose service state
	docker compose ps

logs: ## Follow Compose logs
	docker compose logs -f

backend-dev: ## Run Litestar with reload on the host
	cd backend && DATABASE_URL=$(DATABASE_URL) uv run roots-of-rhythm api --host 127.0.0.1 --port 8000 --reload

frontend-dev: ## Run Next.js development server on the host
	pnpm --dir frontend dev

migrate: ## Apply backend migrations to the local database
	cd backend && DATABASE_URL=$(DATABASE_URL) uv run alembic upgrade head

seed: ## Seed data (implemented in TASK-004)
	@echo "Seed is not implemented until TASK-004" >&2
	@exit 1

format: ## Format backend and frontend sources
	cd backend && uv run ruff format . && uv run ruff check . --fix
	pnpm --dir frontend format

format-check: ## Check formatting without modifying files
	cd backend && uv run ruff format --check .
	pnpm --dir frontend format:check

lint: ## Run backend and frontend linters
	cd backend && uv run ruff check .
	pnpm --dir frontend lint

typecheck: ## Run Python and TypeScript type checks
	cd backend && uv run mypy
	pnpm --dir frontend typecheck

test-unit: ## Run backend and frontend unit tests
	cd backend && uv run pytest -m "not integration"
	pnpm --dir frontend test

test-integration: db-up ## Run PostgreSQL integration tests
	cd backend && TEST_DATABASE_URL=$(DATABASE_URL) uv run pytest -m integration

test-e2e: ## Run Playwright smoke tests against a running stack
	pnpm --dir frontend test:e2e

contract-check: ## Lint OpenAPI and verify generated TypeScript types
	pnpm --dir frontend api:lint
	pnpm --dir frontend api:check

build: ## Build production backend and frontend images
	docker compose build

check: format-check lint typecheck test-unit contract-check build ## Run the local quality baseline
