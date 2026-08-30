# API-контракты

Хранить здесь OpenAPI/AsyncAPI/GraphQL-схемы, примеры и changelog публичных контрактов.

Любое изменение публичного контракта должно одновременно обновлять спецификацию, примеры, changelog и contract-проверки.

## Каталог

- [OpenAPI 3.1](openapi.yaml) — `0.10.1`;
- [API changelog](CHANGELOG.md).

Установленный contract-lint: Redocly (`make contract-check` / `pnpm --dir frontend api:lint`) и drift-check generated TypeScript (`api:check`) против [openapi.yaml](openapi.yaml).
