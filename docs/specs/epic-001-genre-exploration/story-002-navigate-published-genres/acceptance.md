# STORY-002 приёмка TASK-003

Статус: `accepted`

Владелец: Product Owner.

Story: [STORY-002](README.md).  
Task: [TASK-003](tasks.md#task-003-приёмка-навигации-genre).  
Tracker: [#27](https://github.com/K-Mickey/roots-of-rhythm/issues/27).

Дата прогона: 2026-08-19. База кода: `2df974b` плюс правка Vitest (`getByRole` name `/^Jazz$/`, без нетипизированного `exact`).

## Команды и результаты

Стек: `docker compose up -d --build --wait frontend`, `make seed`. Health: backend `/health/ready` `ok`, frontend `/api/health` `ok`.

Первый e2e в этом прогоне поймал not-found Swing: после `make test-integration` корпус не был в БД. После `make seed` повтор: 4 passed.

| Проверка | Результат |
|---|---|
| `make format-check` | pass |
| `make lint` | pass |
| `make typecheck` | pass после замены `{ name: 'Jazz', exact: true }` на `{ name: /^Jazz$/ }` в Vitest (`exact` нет в Testing Library `ByRoleOptions`) |
| backend unit | 69 passed, 9 deselected |
| Vitest | 12 passed |
| backend integration | 9 passed |
| Playwright | 4 passed (`home`, `scaffold`, Swing overview, Swing→Jazz/Jump Blues) |
| OpenAPI | `0.2.0`, без новых operations |

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | Playwright: со Swing клик `link` Jazz (exact) → `/genres/01a0147a-8508-74b7-9689-e7c079b95327`, `h1` Jazz. SSR HTML: `href` на Jazz id, текст `Jazz`. Definition в HTML Jazz: «Американская музыкальная традиция…». |
| AC-2 | pass | Playwright: со Swing клик Jump Blues → `/genres/01a0147a-8508-74b7-9689-e7c272039bac`, `h1` Jump Blues. |
| AC-3 | pass | SSR Jazz: `href` на Swing id, label «Дальнейшее развитие». Chromium: клик `link` Swing (exact) с Jazz → URL Swing, `h1` Swing. |
| AC-4 | pass | Vitest: explanation `Swing developed from Jazz.` не внутри `<a>`. SSR Swing: label «Развился из» не внутри genre `href`; explanation не обёрнут в `/genres/` ссылку. Citation links остаются на sources/external URL. |
| AC-5 | pass | `curl` HTML Swing без браузера: `<a href="/genres/{jazz_id}">Jazz</a>` и Jump Blues; `data-underline="always"`. |
| AC-6 | pass | `GET /genres/00000000-0000-0000-0000-000000000000`: «Материал не найден», UUID нет в `h1`; ссылка «На главную» (STORY-003). |

## NFR

- `NFR-001`: `href` есть в SSR HTML; клиентский переход через `next/link` + `loading.tsx` STORY-001. `GenreRelationsSection` — Client Component (`'use client'`), иначе Mantine `Anchor` не принимает `component={Link}` из RSC.
- `NFR-002`: OpenAPI `0.2.0`; slug/prefetch/граф/поиск/очередь/кэш не добавлялись.
- `NFR-003`: `underline="always"` и `c="pastel.7"`.

## Out of scope (подтверждено)

Нет list/search API, каталога, карты, slug, хлебных крошек, ссылок на Performer/Group/Recording. Главная `/` без `/genres/` ссылок (HOME-0, отдельная story).

## Известные ограничения

- AC-3 не в постоянном Playwright; закрыт curl + одноразовый Chromium клик.
- Playwright `getByRole('link', { name: 'Jazz' })` без `exact` матчит citation «От Jazz Age…»; в e2e используется `exact: true`.
- Redocly `info-license` warning (как в STORY-001/003).
- `make check` на этой машине вызывает pnpm через `npx --yes pnpm@11.19.0`.

## Tracker

Issue TASK-003: [#27](https://github.com/K-Mickey/roots-of-rhythm/issues/27) — закрыт.  
Story: [#23](https://github.com/K-Mickey/roots-of-rhythm/issues/23).

## История

- 2026-08-19: первый прогон приёмки навигации Genre (статус `draft`).
- 2026-08-19: Product Owner принял прогон; статус `accepted`.
