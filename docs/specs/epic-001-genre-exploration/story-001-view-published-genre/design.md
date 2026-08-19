# UI/design specification: public shell и Genre page

Статус: `accepted`

Владелец решения: Product Owner.

Story: [STORY-001](README.md).  
Semantic UI contract (источник наблюдаемого поведения): [ui.md](ui.md) — `accepted`.  
Task checkpoint: [TASK-008](tasks.md#task-008-реализовать-ssr-genre-page-на-nextjs-и-mantine).

Цель: зафиксировать лёгковесную visual/theme specification для application shell, Mantine tokens, page states и representative layouts **до** Genre-specific UI кода. Документ не пересматривает semantic UI contract; он задаёт стартовые визуальные решения. Spacing и точные gaps калибруются на реальном контенте Swing, Jazz и Jump Blues без смены контракта.

## 1. Visual direction

- Продукт: **Roots of Rhythm**.
- Страница Genre — **читательская статья**, не promo landing и не dashboard.
- Светлая схема по умолчанию.
- Не использовать: dark-first, purple/indigo gradient themes, warm cream + terracotta serif, broadsheet/newspaper layout, glow-эффекты, pill-everywhere.
- Chrome: простой **квадратный** (без скругления shell/карточек), современный, с **легчайшими** тенями только там, где нужен лёгкий lift.
- Evidence status: текст и при необходимости иконка; цвет не единственный сигнал ([ui.md](ui.md)).

## 2. Палитра

Холодный пастельный серо-голубой как основа surface; интерфейсный chrome (header) чуть темнее; текст тёмный; ссылки приглушённые.

| Роль | Назначение | Стартовые значения |
|---|---|---|
| Page surface | Фон `body` / main | `#F7FAFC` |
| Surface raised | Контентные карточки / paper на surface | `#FFFFFF` |
| Header / nav chrome | Полоса site header | `#C5D0D8` |
| Footer surface | Компактный footer | `#DDE5EB` (ближе к page, не как header) |
| Text / ink | Основной текст | `#1B242C` |
| Text muted | Вторичный текст, metadata | `#4A5560` |
| Link / citation | Приглушённые ссылки и citation markers | `#3D5A73` |
| Link hover | Hover/focus link | `#2F4558` |
| Border subtle | Разделители, outline карточек | `#B8C4CE` |
| Shadow | Lift для header и relation cards | см. §4 shadows |

Шкала `pastel` для Mantine `colors` (кастомная, без purple):

| Token | Hex |
|---|---|
| `pastel.0` | `#FFFFFF` |
| `pastel.1` | `#F7FAFC` |
| `pastel.2` | `#DDE5EB` |
| `pastel.3` | `#C5D0D8` |
| `pastel.4` | `#A8B6C2` |
| `pastel.5` | `#8A9AAB` |
| `pastel.6` | `#6B7C8F` |
| `pastel.7` | `#3D5A73` |
| `pastel.8` | `#2F4558` |
| `pastel.9` | `#1B242C` |

Маппинг в theme:

- `primaryColor: 'pastel'`
- page `background`: `pastel.1`
- header `background`: `pastel.3`
- footer `background`: `pastel.2`
- body text: `pastel.9`
- links: `pastel.7` → hover `pastel.8`

Контраст текста на header chrome и page surface должен оставаться читаемым (WCAG AA для обычного текста). При калибровке допускается сдвиг соседних ступеней шкалы без смены направления палитры.

## 3. Application shell

```text
header
  ├── project identity: text-link «Roots of Rhythm» → href="/"
  └── «Жанры» → href="/genres" ([STORY-004](../../epic-010-home-search-catalog/story-004-published-genre-catalog/ui.md))
main
  └── page content (каталог на /genres; Genre article на /genres/{id}; HOME-0 на /)
footer
  └── © {current calendar year}, по центру
```

### Правила

- Landmarks: top-level `header`, `main`, `footer`.
- Единственный page `h1` живёт внутри `main`, не в header.
- Primary navigation slot в STORY-001 **пустой и не рендерится** (нет пустого `<nav>` и визуального reserved gap). Ссылка «Жанры» добавляется [STORY-004](../../epic-010-home-search-catalog/story-004-published-genre-catalog/ui.md).
- Identity ведёт на `/`. Stub `href="#"` STORY-001 снят в [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md).
- Header chrome (identity и будущая nav) почти на всю ширину viewport с горизонтальным отступом `md`; ширина статьи `52rem` на chrome не распространяется.
- Footer компактный: только © год по центру, без имени продукта. Sources не переносятся в footer ([ui.md](ui.md)).
- Год берётся на момент render (calendar year), без хардкода устаревшего значения в спецификации.

## 4. Mantine theme tokens (стартовые)

Реализация — `createTheme` как единый источник colors, typography, spacing, radii, shadows, breakpoints ([ADR-0004](../../../decisions/0004-application-stack.md)).

| Token area | Стартовое решение |
|---|---|
| `defaultRadius` | `0` (квадратный chrome). Исключение `xs` только если конкретный Mantine control иначе ломается — с кратким комментарием в коде |
| `shadows.xs` | `0 1px 2px rgba(27, 36, 44, 0.06)` |
| `shadows.sm` | `0 1px 3px rgba(27, 36, 44, 0.08)` |
| Shadows usage | Header bar: `xs`; relation card: `xs` или `sm`; без md+ и glow |
| `fontFamily` | Humanist sans для reading UI, например `"Source Sans 3", "Source Sans Pro", "Segoe UI", sans-serif` (не Inter/Roboto/Arial как brand story) |
| `headings.fontFamily` | Тот же стек; `fontWeight: 600` |
| Heading scale | `h1` Genre name → section `h2` → subsection `h3` (formation) |
| `fontSizes` | Опора на Mantine default; body комфортный для статьи |
| `spacing` | Mantine default; semantic gaps ниже |
| `breakpoints` | Mantine defaults; переключение колонок — по доступной ширине контейнера ([ui.md](ui.md)), не по названию устройства |
| Content width | Статья: `Container` size ≈ `52rem` (калибровка в диапазоне 48–56rem на seed pages). Header/footer: `Container fluid` + `px="md"` |

### Semantic gaps (калибруемые)

| Gap | Назначение | Старт |
|---|---|---|
| Shell vertical | Header / main / footer padding | `md` |
| Section gap | Между Group 1 / 2 / 3 | `xl` |
| Block gap | Между блоками внутри overview | `md` |
| Card internal | Relation card padding | `md` |
| Bibliography row | Между Source entries | `sm` |

Изменение этих gaps при visual review не меняет UI contract, пока сохраняются порядок, landmarks и правила скрытия optional секций.

## 5. Page states (визуально)

Семантика состояний — [ui.md §4](ui.md); здесь только presentation.

| State | Presentation |
|---|---|
| Loading (client navigation) | Skeleton: полоса header + несколько линий content; `aria-busy` / status; без fake значений |
| Loaded | Required блоки + только заполненные optional; optional **отсутствуют в DOM** |
| Empty optional | Нет heading/card/placeholder |
| Not found | Один экран «Материал не найден»; без утечки name; ссылка «На главную» на `/` |
| Page error (overview fail) | `Alert` + retry control; без stale/invented data |
| Section error (relations/sources) | Inline `Alert` + retry **в секции**; overview остаётся видимым |
| Broken optional image | Без browser broken-icon; текстовый layout цел |

Первый SSR HTML содержит основное содержание без обязательной client-only интерактивности (`NFR-002`).

## 6. Representative layouts

### Narrow (одна колонка)

```text
┌─ header: Roots of Rhythm (/) ─────────────┐
├─ main ────────────────────────────────────┤
│  h1 Name                                  │
│  [optional image]                         │
│  period                                   │
│  definition                               │
│  historical / formation                   │
│  features                                 │
│  ── Relations ──                          │
│  relation card…                           │
│  ── Sources ──                            │
│  source row…                              │
├─ footer:           © year                 ┤
```

### Wide (адаптивная сетка по ui.md)

```text
┌─ header ──────────────────────────────────┐
├─ main (Container ~52rem) ─────────────────┤
│  identity row:                            │
│    left: name, period, definition         │
│    right: image (если есть; иначе full)   │
│  context row (если обе секции есть):      │
│    historical | features                  │
│  Relations — full width                   │
│  Sources — full width linear list         │
├─ footer ──────────────────────────────────┤
```

В STORY-001 future sections справа от Relations отсутствуют: Relations на всю ширину Group 2.

### Seed pages для visual review (после кода)

| Genre | URL path |
|---|---|
| Swing | `/genres/01a0147a-8508-74b7-9689-e7c133e4e7a5` |
| Jazz | `/genres/01a0147a-8508-74b7-9689-e7c079b95327` |
| Jump Blues | `/genres/01a0147a-8508-74b7-9689-e7c272039bac` |

## 7. Mantine component mapping

Использовать Mantine; не создавать собственные Button/Input/Modal/базовую typography scale.

| Need | Mantine / semantic |
|---|---|
| Shell landmarks | Semantic `header`/`main`/`footer` + `Box`/`Group`; не обязателен полный `AppShell` |
| Content width | `Container` |
| Titles / body | `Title`, `Text` |
| Identity link | `Anchor` `href="/"` |
| Image | `Image` (+ graceful broken state) |
| Lists | `List` / semantic `ul`/`ol` для features, relations, sources |
| Relation card | `Paper`/`Box` + лёгкая shadow, `radius={0}` |
| Errors | `Alert` + `Button` retry |
| Loading | `Skeleton` |
| Citation links | `Anchor` к якорям Sources / external URL |

CSS Modules — только если предметную композицию нельзя ясно выразить Mantine API. Tailwind и параллельные design systems не подключаются.

## 8. Out of scope

- Figma-макет как обязательный артефакт
- Dark mode toggle
- Localization
- Related Genre detail links / hover affordance ссылки — см. [STORY-002](../story-002-navigate-published-genres/README.md)
- Graph/map visuals, search/catalog chrome
- Содержание главной `/` — см. [STORY-003](../../epic-010-home-search-catalog/story-003-minimal-home/README.md)
- Genre-specific UI код до статуса `accepted` у этого документа

## 9. Checkpoint

Документ утверждён Product Owner. Можно реализовывать theme + shell primitives, затем Genre page по [TASK-008](tasks.md).

## История изменений

- 2026-08-19: калибровка — page surface осветлён до `#F7FAFC`, raised `#FFFFFF`.
- 2026-08-19: Product Owner утвердил design specification (статус `accepted`).
- 2026-08-19: черновик design specification для TASK-008 checkpoint (пастельный серо-голубой, square chrome, header stub `#`, footer с годом).
- 2026-08-19: STORY-003 заменила identity stub `#` на `href="/"`.
- 2026-08-19: header/footer chrome на всю ширину с `px="md"`; footer — только © год по центру.
- 2026-08-19: STORY-004 добавила ссылку «Жанры» на `/genres`.
