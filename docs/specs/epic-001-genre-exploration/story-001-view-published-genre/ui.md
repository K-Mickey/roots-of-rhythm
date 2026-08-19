# UI contract: публичная страница Genre

Статус: `accepted`

Story: [STORY-001](README.md).

Цель: определить наблюдаемое представление страницы Genre до выбора frontend framework, CSS-системы и HTTP API.

## 1. Информационная архитектура

### Общий application shell

```text
Site header
  ├── project identity
  └── primary navigation slot — conditional, empty in STORY-001

Main
  └── Genre article
      ├── Group 1: overview
      ├── Group 2: relations and related content
      └── Group 3: sources

Site footer
  ├── project identity
  └── future legal/secondary navigation slots
```

`header → main → footer` не является устаревшим визуальным шаблоном: это семантическая структура landmark regions. Site header и page overview — разные уровни; page title остаётся внутри `main`.

Navigation slot предусматривается в shell/component contract, но пустой `<nav>` и визуальный отступ не рендерятся. До появления home route project identity не маскируется под неработающую ссылку.

Site footer не содержит Sources: источники относятся к содержанию Genre и остаются внутри `main`. В STORY-001 footer может быть компактным и содержать только project identity; его расширение относится к общему application shell.

### Group 1: overview

```text
Narrow container reading order
  1. Genre name
  2. primary image optional
  3. period optional
  4. definition
  5. historical/origin context optional
  6. characteristic features optional

Wide container
  identity row:
    left  — name, period, definition
    right — primary image, if present

  context row:
    historical/origin context | characteristic features
```

Обе строки принадлежат одной смысловой группе. На широком контейнере image занимает меньшую правую долю и выравнивается по началу; без image левая часть занимает всю доступную ширину. Исторический контекст и признаки переходят в две колонки только когда обе секции присутствуют и сохраняют читаемую ширину. Иначе они занимают одну колонку или растягиваются на всю строку.

Formation входит в historical context как именованный подраздел, если материала достаточно. Это предотвращает дробление короткого текста на множество карточек.

Изображение сохраняет естественное соотношение сторон и ограничивается контейнером; STORY-001 не требует принудительного crop. Очень высокое или широкое изображение не определяет ширину текстовой колонки.

### Group 2: relations and future sections

```text
Narrow container
  Genre relations
  available future sections

Wide container when both areas exist
  Genre relations | future sections stack
```

Это адаптивная сетка, а не две постоянные колонки:

- если future sections отсутствуют, Relations занимают всю ширину;
- если Relations отсутствуют, доступные future sections занимают всю ширину;
- если обе области существуют и минимальная читаемая ширина соблюдена, они образуют две колонки;
- при длинных explanations или недостаточной ширине layout возвращается к одной колонке;
- future sections являются независимыми блоками в правой области и не получают искусственную равную высоту с Relations.

В STORY-001 справа нет placeholders: seed показывает Relations на всю ширину Group 2.

### Group 3: sources

Sources занимают отдельную полную строку после Group 2. Bibliographic entries остаются линейным списком: это лучше сохраняет связь citation marker → Source и не заставляет читать длинные titles/locators по газетным колонкам.

### Компактность без перегрузки

- компактность означает эффективную группировку контента, а не сжатие текста или отказ от воздуха между смысловыми блоками;
- группы отделяются меньшим вертикальным интервалом, чем самостоятельные страницы, но сохраняют визуально различимые headings;
- основной narrative text ограничивает длину строки, а не растягивается на весь широкий монитор;
- metadata и короткие features могут использовать доступную ширину плотнее;
- две колонки включаются по объёму доступного контейнера, а не по названию устройства;
- empty grid tracks схлопываются и не оставляют половину страницы пустой.

Точные spacing tokens, gaps и max-width не фиксируются до реализации. Они калибруются на реальном контенте Swing, Jazz и Jump Blues и на разных ширинах viewport. Изменение отступов в рамках утверждённой иерархии считается визуальной доводкой, а не изменением контракта, пока сохраняются читаемость, accessibility, порядок и правила адаптивности.

### Порядок внутри main

```text
Group 1: name/image/period/definition/history/features
Group 2: relations/future content
Group 3: sources
```

Правила:

- на странице ровно один `h1` — Genre name;
- definition находится в первой группе и отвечает на вопрос «что это?» до длинного материала;
- period является краткой metadata; объяснение периода относится к historical context;
- geography и formation не создают пустые заголовки;
- будущие content slots входят в общую архитектуру Genre page, однако STORY-001 не создаёт для них карточки, fixtures или placeholders;
- Sources располагаются после содержательных секций, но конкретный Claim имеет локальную ссылку на использованное Evidence;
- оглавление и sticky navigation не нужны для короткой страницы первой версии.

### Обязательные и опциональные блоки

| Блок | Обязательность | Поведение при отсутствии |
|---|---|---|
| Genre name | required | Genre нельзя опубликовать |
| Definition | required | Genre нельзя опубликовать |
| Primary image | optional | область изображения не создаётся |
| Period | optional | metadata не показывается |
| Geography/origin | optional | секция скрывается |
| Formation | optional | секция скрывается |
| Characteristic features | optional | секция скрывается |
| Genre relations | optional | секция скрывается |
| Performer/Group/examples/dances/Stories | optional, future | секции скрываются |
| Sources | optional | общий список скрывается; evidence status Claims остаётся видимым |

Скрытая секция означает отсутствие DOM-блока и заголовка, а не пустую карточку «данных пока нет». Редакторская полнота относится к будущему Editor UI.

## 2. Представление Genre relations

### Базовый формат

STORY-001 использует вертикальный список текстовых relation cards, а не мини-граф. Каждая карточка содержит:

1. пользовательский label relation с учётом перспективы текущего Genre;
2. name связанного Genre;
3. explanation полностью, без обязательного раскрытия;
4. temporal context;
5. geographic context;
6. evidence status;
7. references на прошедшее review Evidence, если они есть.

Карточка не показывает внутренние `editorial_status`, provenance, audit author/time или IDs. Public Discovery уже гарантирует публикацию relation и обоих endpoint Genre.

До реализации detail routes имя связанного Genre отображается обычным текстом, а не ссылкой и не элементом с ложным hover/focus affordance. Снято [STORY-002](../story-002-navigate-published-genres/ui.md) (`draft`): имя становится ссылкой на `/genres/{genre_id}`.

### Perspective labels

В базе хранится relation type и направление. UI не хранит отдельные типы для обратного направления, а выбирает label по роли текущего Genre:

| Relation type | Текущий Genre — subject | Текущий Genre — target |
|---|---|---|
| `influenced` | «Повлиял на» | «Влияние со стороны» |
| `contributed_to_emergence_of` | «Участвовал в формировании» | «Источники формирования» |
| `developed_from` | «Развился из» | «Дальнейшее развитие» |
| `overlaps_with` | «Пересекается с» | тот же label; relation симметрична |
| `revival_of` | «Возрождение традиции» | «Позднейшее возрождение» |

Label всегда сопровождается explanation. Он не используется как самостоятельное историческое утверждение.

### Seed presentation

На странице Swing:

- «Развился из — Jazz»;
- «Участвовал в формировании — Jump Blues».

Обе карточки показывают explanation, приблизительный период, географический контекст и статус `supported` с citations.

### Порядок

В первой версии relations не группируются в отдельные деревья. Они сортируются по началу temporal context; при равенстве — по стабильному relation type order и имени связанного Genre. Точный алгоритм сравнения приблизительных периодов определяется data contract.

## 3. Evidence status и источники

### Общие правила

- статус выражается текстом и, при необходимости, иконкой; цвет не является единственным сигналом;
- explanation и evidence status видны без раскрытия дополнительной панели;
- Evidence reference ведёт к записи в секции Sources или открывает доступный внешний locator;
- одинаковый Source в нескольких Claims один раз присутствует в общем списке, но каждая relation сохраняет собственные references и evidence roles;
- внешний URL не является единственным отображаемым значением Source: показываются доступные bibliographic metadata.

### `supported`

Пользовательский label: «Подтверждено источниками».

UI показывает минимум одну прошедшую review reference с ролью `supports`. Наличие ссылки без прошедшего review не создаёт этот статус.

### `unverified`

Пользовательский label: «Пока не подтверждено источниками».

Статус не скрывается при отсутствии Evidence. Формулировка не должна звучать как «ложно»: она сообщает только состояние подтверждения.

### `disputed`

Пользовательский label: «Есть существенные разногласия».

UI показывает explanation разногласия и прошедшее review Evidence с ролью `opposes`. Если есть supporting Evidence, роли источников визуально и текстово различаются.

### Общая секция Sources

Для каждого доступного Source отображаются:

- title;
- author или responsible organization, если известны;
- publication/date, если известны;
- locator или external link, если разрешён;
- связь с Claims через citation markers.

Цитата или SourceFragment не раскрываются целиком, если rights/access policy этого не разрешает.

## 4. Состояния страницы

### Loading

- при client-side navigation используется skeleton, повторяющий header и несколько строк содержания;
- контейнер получает доступный признак загрузки;
- skeleton не имитирует реальные значения и не озвучивается как содержимое;
- первая загрузка должна оставаться содержательно доступной без интерактивной карты и обязательного client-side JavaScript согласно NFR-002.

### Loaded

Показываются required блоки и только заполненные optional секции. Порядок не меняется в зависимости от количества данных.

### Empty optional section

Секция полностью отсутствует. Это состояние отличается от ошибки загрузки: технический сбой нельзя молча представить как отсутствие данных.

### Not found

Неизвестный, draft, archived и другой непубличный Genre дают один публичный экран «Материал не найден». UI не объясняет, существует ли скрытый объект, и не показывает его name.

Экран содержит безопасный путь назад; глобальная навигация или каталог добавляются соответствующей story EPIC-010.

### Page error

При невозможности получить обязательные данные показывается общий error state с возможностью повторить запрос. Старые или выдуманные данные вместо ошибки не показываются.

### Partial projection error

В STORY-001 Genre page загружает overview, relations и sources отдельными API responses. Ошибка overview даёт page error, поскольку без identity/definition страница не имеет смысла. Сбой relations или sources даёт в своей секции явное error/retry state, но не скрывает уже полученный overview. Техническая ошибка не маскируется как пустой успех.

### Broken optional image

Не показывается browser broken-image icon. Контент остаётся доступным в текстовом layout; факт сетевой ошибки не превращается в сохранённое «изображение отсутствует».

## 5. Responsive и accessibility

### Семантика

- top-level `header`, `main` и `footer` формируют application shell;
- условный `nav` создаётся только при наличии навигационных ссылок и получает понятное имя;
- `main` содержит единственный основной контент страницы Genre;
- `article` или эквивалентная семантическая область объединяет содержание;
- один `h1`, секции используют последовательные `h2/h3`;
- Sources имеют собственный именованный section;
- списки relations, features и sources размечаются как списки, а не набор визуальных `div` без структуры.
- три content groups не обязаны становиться дополнительными landmark regions: избыточное количество landmarks ухудшает навигацию.

### Keyboard и focus

- весь контент читается без pointer device;
- citation links и будущие раскрываемые элементы доступны с клавиатуры;
- focus indicator не отключается;
- неактивное имя связанного Genre не получает `tabindex` и роль ссылки.

### Не только визуальные сигналы

- evidence status имеет текст, а не только цвет;
- направление relation имеет label, а не только стрелку;
- приблизительность периода выражается текстом/семантикой, а не только пунктиром;
- изображение имеет alt text и не заменяет definition.

### Адаптивность

- mobile layout одноколоночный;
- mobile-first reading order: name, image, period, definition, historical context, features;
- на широком контейнере image переносится в правую колонку визуально, не нарушая логический reading order;
- Group 1 и Group 2 включают две колонки только при достаточной ширине содержимого;
- отсутствующая колонка схлопывается, а существующий блок занимает доступную ширину;
- relation cards не требуют горизонтальной прокрутки;
- длинные title/URL источников переносятся и не ломают layout;
- основной текст сохраняет комфортную длину строки на широком экране;
- breakpoints определяются поведением контента, а не классами устройств;
- значимые анимации не требуются; предпочтение reduced motion соблюдается, если анимации появятся позже.

## 6. Семантические данные для UI

Это не JSON schema и не HTTP contract. UI требуется следующий смысловой view model.

### GenrePageView

```text
GenrePageView
├── id
├── name
├── definition
├── primary_image optional
├── period optional
├── geography_or_origin optional
├── formation optional
├── characteristic_features[]
├── relations[]
├── future section summaries[] absent in STORY-001
└── sources[]
```

### GenreRelationView

```text
GenreRelationView
├── id
├── related_genre: id + name
├── relation_type
├── perspective: subject | target | symmetric
├── explanation
├── temporal_context
├── geographic_context
├── evidence_status
└── evidence_references[]
```

`perspective` является read-model понятием, а не новым domain enum. Оно позволяет UI корректно выбрать label без получения и интерпретации всего Claim graph.

### EvidenceReferenceView

```text
EvidenceReferenceView
├── source_id
├── role: supports | opposes | context
└── locator availability
```

`citation_marker` является вычисляемым UI-значением: frontend получает его из позиции `source_id` в упорядоченном `sources[]`. API не хранит цитационный номер как отдельную истину.

Public view model не содержит draft objects, внутренние review notes, audit metadata или authorization flags. UI не является последней линией защиты от раскрытия непубличных данных.

`GenrePageView` — составная frontend model, а не HTTP response. UI собирает её из `GenreOverviewResponse`, `GenreRelationsResponse` и `GenreSourcesResponse`, сохраняя независимые loading/error states секций.

## Трассировка к STORY-001

| UI requirement | Story |
|---|---|
| required name/definition и скрытые empty sections | FR-002–FR-004, AC-1–2 |
| relation cards и perspective labels | FR-006, FR-008–FR-010, AC-3, AC-7–8 |
| evidence presentation | FR-007, AC-4–6 |
| единый not-found | FR-005, AC-9 |
| no-JS/readable и accessibility | NFR-002, NFR-006 |
| отсутствие инфраструктурных предположений | NFR-004–NFR-005 |

## Не входит в UI contract STORY-001

- визуальный graph/map;
- переходы на страницы связанных Genre;
- Editor controls и отображение draft completeness;
- формы создания и публикации;
- search/catalog navigation;
- локализация;
- карточки Performer, Group, Recording, Dance или Story;
- playback и streaming embeds;
- точные colors, typography tokens, component library и CSS breakpoints.

## Принятые решения

Product Owner подтвердил весь UI contract 2026-08-16, включая:

1. application shell `site header → main → site footer`, navigation slot без пустого визуального места;
2. три content groups внутри `main`;
3. адаптивные две колонки только при наличии двух областей и достаточной читаемой ширине;
4. Sources внутри `main`, а не в site footer;
5. отсутствие принудительного crop изображения в STORY-001;
6. relation/evidence presentation, page states, accessibility и смысловой UI view model из разделов 2–6;
7. баланс компактности и воздуха с практической калибровкой отступов без изменения смысловой структуры.

## Основания layout review

- [W3C WAI: Page Regions](https://www.w3.org/WAI/tutorials/page-structure/regions/) — header, navigation, main и footer как семантические regions;
- [W3C ARIA APG: Landmarks Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/landmarks/) — landmarks помогают навигации, но их избыток снижает пользу;
- [web.dev: Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) — mobile-first и breakpoints, определяемые содержимым;
- [web.dev: CSS Grid](https://web.dev/learn/css/grid) — `auto-fit` схлопывает пустые tracks и позволяет существующим блокам занять пространство.

## История изменений

- 2026-08-16: Product Owner подтвердил relation/evidence/states/accessibility/view-model решения и предложил общий header/main/footer shell с тремя compact content groups; layout уточнён как adaptive grid без пустых tracks.
- 2026-08-16: уточнённый layout и весь UI contract подтверждены; зафиксирован баланс компактности и воздуха, а точные отступы оставлены на visual calibration с реальным контентом.
- 2026-08-17: после разделения API overview остался обязательным page lifecycle, а relations и sources получили независимые inline error/retry states.
