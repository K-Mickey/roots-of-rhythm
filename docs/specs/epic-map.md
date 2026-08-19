# Черновая карта epics

Статус: `draft`

Цель: определить пользовательские вертикали MVP до формализации первой story. Epic группирует пользовательский результат, а не архитектурный слой.

## Предлагаемые epics

| ID | Tracker | Пользовательский результат | Поддерживаемые вопросы | Зависимости |
|---|---|---|---|---|
| [`EPIC-001`](epic-001-genre-exploration/README.md) | [#1](https://github.com/K-Mickey/roots-of-rhythm/issues/1) | Исследовать жанр и понять его место в истории | CQ-001, CQ-002, CQ-004 | опубликованный Genre, Claims и Evidence |
| `EPIC-002` | [#6](https://github.com/K-Mickey/roots-of-rhythm/issues/6) | Исследовать Performer, Group и Recording | CQ-003, CQ-004, CQ-005, CQ-007 | People/Music Catalog, credits, ListeningGuide |
| `EPIC-003` | [#11](https://github.com/K-Mickey/roots-of-rhythm/issues/11) | Проследить развитие музыки по интерактивной карте | CQ-001, CQ-002, CQ-006 | relations, Discovery projections, фильтры и текстовая альтернатива карты |
| `EPIC-004` | [#3](https://github.com/K-Mickey/roots-of-rhythm/issues/3) | Исследовать связь Dance и Genre | CQ-006 | Dance Catalog, DanceGenreRelation |
| `EPIC-005` | [#12](https://github.com/K-Mickey/roots-of-rhythm/issues/12) | Войти как Editor, создавать, проверять и публиковать знания | обеспечивает все CQ | authentication, Editorial lifecycle, `/studio`, sources и audit |
| `EPIC-006` | [#2](https://github.com/K-Mickey/roots-of-rhythm/issues/2) | Задавать вопросы опубликованному корпусу | CQ-001–CQ-005 | Sources, supported Claims, ingestion, evaluation |
| `EPIC-007` | [#5](https://github.com/K-Mickey/roots-of-rhythm/issues/5) | Читать опубликованные знания через MCP | поддерживает внешние AI-сценарии | стабильные read contracts; `ask_published_corpus` добавляется только после EPIC-006 |
| `EPIC-008` | [#14](https://github.com/K-Mickey/roots-of-rhythm/issues/14) | Получать AI-предложения для редактора | ускоряет наполнение всех CQ | ручной Editorial workflow, AIProposal и evaluation |
| `EPIC-009` | [#7](https://github.com/K-Mickey/roots-of-rhythm/issues/7) | Открывать доступные музыкальные примеры | дополняет CQ-001–CQ-006 | MediaReference и исследование providers |
| `EPIC-010` | [#4](https://github.com/K-Mickey/roots-of-rhythm/issues/4) | Найти точку входа и нужный материал через главную, каталоги и поиск | навигация ко всем CQ | опубликованные сущности, Discovery queries, списки, фильтры и статистика |
| `EPIC-011` | [#13](https://github.com/K-Mickey/roots-of-rhythm/issues/13) | Читать структурированные Stories, сравнения и маршруты | CQ-001, CQ-002, CQ-004, CQ-005 | Story, sections, Claims, entity references и музыкальные примеры |
| [`EPIC-012`](epic-012-production-readiness/README.md) | [#8](https://github.com/K-Mickey/roots-of-rhythm/issues/8) | Безопасно эксплуатировать публичный сервис и своевременно узнавать о проблемах | обеспечивает доступность всех публичных сценариев | стабильная vertical slice, deployment topology и измеримый production baseline |

ID отражает стабильную идентичность epic, а не обязательный порядок реализации.

## Покрытие MVP

| Область MVP | Epic | Комментарий |
|---|---|---|
| Главная и статистика | EPIC-010 | минималистичная, только опубликованный корпус |
| Списки и единый поиск | EPIC-010 | Genre, Performer, Group, Recording, Dance и Story |
| Страница Genre | EPIC-001 | первая вертикаль |
| Страницы Performer, Group, Recording | EPIC-002 | MusicalWork/Release pages отложены |
| Stories | EPIC-011 | отделены от визуальной карты |
| Карта и текстовая альтернатива | EPIC-003 | Dance-layer выключаемый |
| Dance pages и DanceGenreRelation | EPIC-004 | без PracticeFit/DanceRecordingFit |
| Login/logout, current user, editor mode и `/studio` | EPIC-005 | публичная регистрация пока не принята |
| Sources, Evidence и evidence status | EPIC-001/002/004/005/011 | сквозная проверяемость, не отдельный infrastructure epic |
| RAG | EPIC-006 | только утверждённый корпус и citations |
| Read-only MCP | EPIC-007 | базовые tools не обязаны ждать RAG |
| Agent proposals | EPIC-008 | после ручного Editorial workflow |
| Playback links/providers | EPIC-009 | последний этап MVP |
| Abuse/DDoS protection, observability и alerts | EPIC-012 | отдельные work items перед публичным трафиком; не блокируют старт разработки |

## Осознанно не создаём отдельные epics

- PostgreSQL, S3, vector index, queue, worker и search engine являются implementation/ADR concerns внутри пользовательских stories. EPIC-012 является осознанным исключением: он даёт проверяемый результат владельцу/оператору публичного сервиса, а не группирует инфраструктуру по технологии.
- MediaAsset и опциональные основные изображения входят в acceptance criteria соответствующих страниц; загрузка и управление — в EPIC-005. Галереи и автоматические responsive variants отложены.
- Authentication не выделяется в самостоятельный технический epic: он является необходимым срезом Editor journey EPIC-005.
- MCP transport не владеет данными и не получает отдельный domain epic.
- MusicalWork/Release pages, монетизация, публичная социальная функциональность и расширенный Dance domain остаются вне MVP.

## Предлагаемые зависимости и порядок discovery

```text
EPIC-001 Genre vertical slice
  ├── EPIC-002 Performer/Group/Recording
  ├── EPIC-005 Editorial workflow
  └── EPIC-011 Stories

EPIC-001 + EPIC-002 + опубликованный корпус
  ├── EPIC-010 Home/Search
  ├── EPIC-003 Map
  └── EPIC-004 Dance

EPIC-005 + Sources/Evidence
  └── EPIC-006 RAG
       ├── EPIC-007 MCP ask tool
       └── EPIC-008 Agent proposals

EPIC-009 Media providers — завершающий этап MVP

Первая публичная эксплуатация
  └── EPIC-012 Production readiness
       ├── abuse, account/request rate limits и edge DDoS/WAF
       └── observability, uptime и Telegram/email alerts
```

Это не release plan. EPIC-007 read-only tools без RAG могут начаться после стабилизации публичных query contracts.

## Первый vertical slice

`EPIC-001` подтверждён первым epic. Первая формализуемая story:

> Visitor открывает опубликованную страницу Genre Swing, получает краткое определение, доступный исторический контекст, объяснённые связи с другими Genre и видимый evidence status с источниками.

Это вертикальный срез через persistence, domain/application, public query/API и frontend. Он проверяет центральную ценность проекта без карты, RAG, авторизации, media providers и полной редакторской студии.

Performer, Group и Recording не входят в первую story. Связанный Genre показывается как часть relation, но не становится ссылкой до реализации его публичного route. Все принятые relation types и поля поддерживаются моделью; seed не обязан содержать искусственный пример каждого enum value.

## Почему не начинаем с инфраструктуры

- отдельная story «создать все таблицы» не даёт пользовательского результата;
- story «поднять RAG» не имеет утверждённого корпуса;
- карта без объяснимых Claims станет декоративным графом;
- Editorial UI до проверки публичной модели закрепит неизвестные формы;
- playback отложен и не нужен для понимания страницы.

## Вопросы текущего этапа

STORY-001 выполнена и принята 2026-08-19. EPIC-001 остаётся открытым: следующие stories — навигация между Genre, интеграция с EPIC-002 и editorial UI. EPIC-012 не блокировал локальную реализацию, но его обязательные work items по-прежнему блокируют первый публичный трафик.

Подтверждено 2026-08-16: EPIC-001 идёт первым; Performer/Group/Recording и локализация исключены из STORY-001; controlled seed/import допустим; для публикации Genre достаточно `name + definition`; пустые секции скрываются; seed содержит Swing, Jazz и Jump Blues; draft GenreRelation допускает частичное заполнение, publish требует полноты; relation публикуется независимо и имеет вычисляемую visibility; `confidence` исключён.

## История изменений

- 2026-08-17: добавлен EPIC-012 Production readiness; отдельно зафиксированы abuse/DDoS protection и observability/alerts.
- 2026-08-17: bootstrap GitHub tracker добавлен как обязательный gate перед реализацией.

- 2026-08-16: добавлен EPIC-010 для главной/search/catalog navigation.
- 2026-08-16: Stories выделены из EPIC-003 в EPIC-011; EPIC-003 оставлен картой.
- 2026-08-16: уточнены границы Editorial, MCP, MediaAsset и инфраструктурных non-epics.
- 2026-08-16: EPIC-001 выбран первым; первая story сокращена до Genre и Genre relations, добавлены локализация и controlled seed.
- 2026-08-16: локализация удалена из EPIC-001 и перенесена в deferred scope; controlled seed сохранён.
- 2026-08-16: подтверждены минимальная публикация Genre, скрытие пустых секций и три Genre seed; lifecycle relation вынесен в DDD Workshop 005.
- 2026-08-16: подтверждены два seed Claims и институциональные Evidence; EPIC-001/STORY-001 переведены в `accepted`.
- 2026-08-16: UI и OpenAPI `0.1.0` STORY-001 утверждены; текущий этап переведён к архитектурным решениям.
- 2026-08-19: STORY-001 принята Product Owner; статус story `done`.
