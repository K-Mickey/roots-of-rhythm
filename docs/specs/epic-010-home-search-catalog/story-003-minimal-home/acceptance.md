# STORY-003 приёмка TASK-002

Статус: `accepted`

Владелец: Product Owner.

Story: [STORY-003](README.md).  
Task: [TASK-002](tasks.md#task-002-приёмка-home-0).  
Tracker: [#29](https://github.com/K-Mickey/roots-of-rhythm/issues/29).

Дата прогона: 2026-08-19. База кода: `4819532` плюс Makefile (`PNPM` fallback) и `AppShell` на CSS grid `auto 1fr auto` в коммите TASK-002.

## Команды и результаты

Стек: `make up` + `make seed`. Health: backend `/health/ready` `ok`, frontend `/api/health` `ok`.

На хосте нет `pnpm` в PATH. После правки Makefile frontend-команды идут через `npx --yes pnpm@11.19.0`.

| Проверка | Результат |
|---|---|
| `make format-check` | pass (Ruff + Prettier) |
| `make lint` | pass (Ruff + ESLint) |
| `make typecheck` | pass (mypy 94 files, `tsc`) |
| backend unit (`pytest -m "not integration"`) | 69 passed, 9 deselected |
| Vitest | 12 passed (6 files) |
| OpenAPI Redocly | valid; 1 warning `info-license` (не блокирует) |
| `openapi-typescript` drift | pass |
| Compose production images | built; containers healthy |
| Playwright (`home` + `scaffold` + Swing) | 3 passed против `127.0.0.1:3000` / `:8000` после rebuild frontend |

Первый прогон Swing e2e после `4819532`: `h1` Swing в DOM, но Playwright `hidden`. Причина — `main` как flex container: Mantine `Container` имеет `margin-inline: auto`, поэтому во flex он получает shrink-to-fit ширину, а `container-type: inline-size` на Genre Container и percentage-ширины в `loading.tsx` не дают intrinsic width, и ширина падала до padding. Итоговое решение: `AppShell` — CSS grid `grid-template-rows: auto 1fr auto`, `main` остаётся block container (page Containers снова на всю ширину), главная центрируется `height: 100%` + flex внутри `main`. Genre page код не менялся.

Измерения Chromium 1280×800: `main` 690.9px, группа title+слоган — 303px сверху и 303px снизу (симметрично). 390×780: 279/279, `h1` 242px без обрезки. Genre Container 832px (52rem), `article` 800px, `h1` Swing видим. Not-found: `h1` и ссылка 800px.

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | `GET /`: `h1` Roots of Rhythm (34px) и слоган «История музыки для тех кто танцует и слушает». Измеренные отступы группы в `main` равны сверху и снизу (303/303 при 1280×800, 279/279 при 390×780). Playwright `home.spec.ts`. |
| AC-2 | pass | HTML `/`: нет `href` на `/genres/`, нет Jazz / Swing / Jump Blues. Playwright: `a[href*="/genres/"]` count 0. |
| AC-3 | pass | HTML `/`: нет `HomeStatistics`, `<nav>`, поиска. Страница не вызывает API (`page.tsx` без `fetch`). |
| AC-4 | pass | Header identity `href="/"` на `/` и на seed Swing. Stub `href="#"` отсутствует. Playwright проверяет атрибут identity на главной. |
| AC-5 | pass | `GET /genres/00000000-0000-0000-0000-000000000000`: «Материал не найден», ссылка «На главную» на `/`. Playwright клик → `/`. |
| AC-6 | pass | `curl` HTML `/` без браузера содержит `h1` Roots of Rhythm и слоган (статический route `○ /`). |

## NFR

- `NFR-001`: содержание `/` в первом HTML, без обязательного page JS для чтения названия и слогана.
- `NFR-002`: OpenAPI `0.2.0` без новых operations; Elasticsearch/кэш/очередь/граф/auth не добавлялись.
- `NFR-003`: тексты из `frontend/src/shared/shell/product.ts`.

## Out of scope (подтверждено)

На `/` нет каталога Genre, HOME-1/HOME-2 chrome, list API. Каталог жанров — следующая story EPIC-010.

## Известные ограничения

- Visual review узкий/широкий viewport без приложенных скриншотов; центрирование подтверждено измерением bounding boxes, не pixel-perfect screenshot pack.
- `loading.tsx` Genre page не покрыт автоматической проверкой ширины: регрессия shrink-to-fit была видна только в ручном осмотре DOM.
- Клик identity со страницы Swing в Playwright не отдельный шаг: тот же `href="/"`, что на `/`.
- Redocly warning `info-license`.
- `make check` на этой машине тянет pnpm через `npx --yes pnpm@11.19.0` (npm warn `devdir`); каноничен PATH/`corepack`, когда pnpm установлен.

## Tracker

Issue TASK-002: [#29](https://github.com/K-Mickey/roots-of-rhythm/issues/29) — закрыт.  
Story: [#24](https://github.com/K-Mickey/roots-of-rhythm/issues/24).

## История

- 2026-08-19: первый прогон приёмки HOME-0 (статус `draft`).
- 2026-08-19: Product Owner принял прогон; статус `accepted`.
