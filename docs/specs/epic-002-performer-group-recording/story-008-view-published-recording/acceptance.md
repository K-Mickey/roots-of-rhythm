# STORY-008 приёмка TASK-007

Статус: `draft`

Владелец: Product Owner.

Story: [STORY-008](README.md).  
Task: [TASK-007](tasks.md#task-007-seed-и-приёмка-story-008).  
Tracker: story [#34](https://github.com/K-Mickey/roots-of-rhythm/issues/34), task [#55](https://github.com/K-Mickey/roots-of-rhythm/issues/55).

Дата прогона: 2026-08-30. База кода: `b7fff94` (TASK-007A) плюс локальные изменения TASK-007B.

## Команды и результаты

Стек: `make up`, `make migrate`, `make seed` дважды. Backend `/health/ready` и frontend `/api/health` отвечают успешно.

| Проверка | Результат |
|---|---|
| `make seed` дважды | pass; оба запуска завершились без дублирования |
| `make test-unit` | pass: backend 201, frontend 49 |
| `make test-integration` | pass: 35 |
| `make contract-check` | pass; OpenAPI `0.10.1`, 8 известных Redocly warnings |
| `make test-e2e` | pass: 13 |
| `make check` | pass; format, lint, mypy/TypeScript, backend unit 201, frontend unit 49, contract checks and production builds passed |
| `git diff --check` | passed |

Ручная проверка API и SSR:

- `GET /api/v1/recordings` — 5 published Recording: три `Sixteen Tons` и две `Nobody Knows the Trouble I've Seen`;
- detail Recording — `200`; Ford содержит ListeningGuide, Merle — `first_recording_of`, Stevie Wonder — неизвестный период, Marian Anderson 1924 раскрывает public-domain English body и русский reading translation;
- `GET /api/v1/songs/{sixteen_tons_id}` — 3 Recording, facets `Country (2)` и `Rhythm and Blues (1)`;
- неизвестный Recording API id — `404 RECORDING_NOT_FOUND`;
- SSR `/recordings`, Ford detail и direct Song query — `200` и содержат ожидаемые данные;
- неизвестный SSR Recording показывает «Запись не найдена»; Next.js возвращает HTML shell со статусом 200;
- Playwright: каталог содержит ссылки Recording/Person/Genre; Ford detail содержит Work, texts и ListeningGuide; spiritual detail переключает тексты через query/back; mobile Song и Recording detail не имеют page overflow.

## Acceptance criteria

| AC | Вердикт | Evidence |
|---|---|---|
| AC-1 | pass | Playwright `recording-detail.spec.ts`; Recording API integration |
| AC-2 | pass (tests) | `SongPageContent.test.tsx`: одна Recording в центре, chronology отсутствует; отдельного seed Work с одной Recording нет |
| AC-3 | pass | Playwright `song-recordings.spec.ts`: chronology, client navigation, query и сохранение window state |
| AC-4 | pass | domain/application tests публикации без primary credit или Work usage |
| AC-5 | pass (tests) | domain medley ordering; Discovery и selection tests исключают medley из facets; seed medley отсутствует |
| AC-6 | pass | seed facets Country/R&B; integration и Playwright filtering/counts |
| AC-7 | pass | Merle badge появляется только из supported Claim; UI не использует общий label «Оригинал» |
| AC-8 | pass (tests) | seed доказывает `first_recording_of`; остальные predicates и точные labels покрыты origin domain/projection и `labels.test.ts` |
| AC-9 | pass | Ford seed содержит performable English и published machine reading translation; spiritual seed содержит раскрытые public-domain bodies; Playwright переключает `text` без reload на Song и Recording detail |
| AC-10 | pass | Playwright: header «Записи», каталог и ссылки Recording/Person/Genre |
| AC-11 | pass | Playwright unknown Recording; API unknown Recording 404 |
| AC-12 | pass | Playwright: ListeningGuide виден на Ford Recording и в выбранном Recording block Song page |

## NFR

- `NFR-001`: direct Recording/Song URLs содержат SSR content; invalid query нормализуется безопасно.
- `NFR-002`: API и страницы публичны, pagination/player/search infrastructure не добавлены.
- `NFR-003`: collections рендерятся без фиксированного maximum.
- `NFR-004`: Recording, Genre и Lyrics tabs доступны как links/tabs; push, replace и back/forward проверены Playwright.
- `NFR-005`: viewport 390×844 — chronology выше Recording, document не имеет horizontal overflow.

## Test-only и ограничения corpus

- Single-Recording layout подтверждён component test, но отдельного seed Work с одной Recording нет.
- Medley и исключение его Genre из facets подтверждены domain/Discovery/frontend tests, но medley в seed отсутствует.
- Seed содержит только supported `first_recording_of`; три остальных origin predicates проверены без browser corpus.
- Fallback lyrics warning проверен на spiritual corpus: две Recording используют Work fallback с `confirmed_for_recording=false`; предупреждение не выводится для body, скрытого по правам.
- Sixteen Tons bodies отсутствуют по copyright policy; public-domain spiritual English body и проектный русский reading translation раскрываются.
- Release/Track, player, duration и first release date остаются вне STORY-008.

## Известные предупреждения

- Redocly: `info-license`; отсутствие 4XX у list endpoints; example Sixteen Tons ещё не содержит обязательные `recording_genres` и `recordings`. Contract generation drift отсутствует.
- Первый browser-прогон выявил и после исправления закрыл передачу `next/link` из server component и mobile overflow header.

## Tracker

Story [#34](https://github.com/K-Mickey/roots-of-rhythm/issues/34) и task [#55](https://github.com/K-Mickey/roots-of-rhythm/issues/55) не закрываются автоматически. Документ остаётся `draft` до утверждения Product Owner.

## История

- 2026-08-30: controlled Recording corpus, browser acceptance и итоговый прогон STORY-008.
