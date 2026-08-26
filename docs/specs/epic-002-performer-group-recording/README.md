# EPIC-002: исполнители, песни, записи и релизы

Статус: `draft`

Tracker: [GitHub issue #6](https://github.com/K-Mickey/roots-of-rhythm/issues/6). Stories: [STORY-005 #31](https://github.com/K-Mickey/roots-of-rhythm/issues/31), [STORY-006 #32](https://github.com/K-Mickey/roots-of-rhythm/issues/32), [STORY-007 #33](https://github.com/K-Mickey/roots-of-rhythm/issues/33), [STORY-008 #34](https://github.com/K-Mickey/roots-of-rhythm/issues/34), [STORY-009 #35](https://github.com/K-Mickey/roots-of-rhythm/issues/35), [STORY-010 #36](https://github.com/K-Mickey/roots-of-rhythm/issues/36).

Приоритет поставки: после Genre vertical slice (EPIC-001) и точки входа HOME-0 / каталог Genre (EPIC-010 STORY-003/004).

## Пользовательский результат

Visitor исследует опубликованных исполнителей и группы, читает **песню** как авторское произведение, открывает и сопоставляет её **конкретные записи** разных исполнителей, языков и жанров и переходит к **релизам** — без авторизации и без обязательного плеера.

## Поддерживаемая ценность

- CQ-003, CQ-004, CQ-005, CQ-007;
- связать Genre с людьми, песнями, записями и изданиями;
- не смешивать песню, запись, дорожку и альбом.

## Объекты и связи

Доменные имена: Performer (Person), Group, MusicalWork (UI: Песня), Recording (Запись), Release (Релиз), Track (не страница).

```text
Genre <--ClassificationAssignment--> Performer | Group | MusicalWork | Recording | Release
MusicalWork 1 -- * RecordingWorkUsage * -- 1 Recording   (публикация Recording требует >=1 usage)
MusicalWork 1 -------- * LyricsVersion
Recording * --RecordingCredit-- * Performer|Group   (>=1 primary)
Recording * -- Track -- * Release      (Track — join; владелец агрегата Release)
Performer * -- GroupMembership -- * Group
```

- Песня может быть без записей (секция скрыта).
- Запись без хотя бы одного published Work usage публиковать нельзя.
- Обычная запись использует один Work; partial performance и medley выражаются `RecordingWorkUsage`.
- Запись без релиза можно.
- Одна запись может быть на нескольких релизах.
- Жанр песни, записи и релиза не наследуется автоматически.
- Страница песни отдельно показывает подтверждённую классификацию Work и вычисляемые фасеты жанров Recording.
- Авторы Work — WorkCredit; исполнители появляются через RecordingCredit. Исполнители/группы релиза остаются related-списками до ReleaseCredit.
- Все Recording одного Work равноправны. Хронология не создаёт `is_original`; виды исторического первенства задаются Claims.
- «Послушать» на песне показывает **запись**, не отдельный аудио-объект. Плеер — EPIC-009. ListeningGuide — на странице записи.
- Каталога записей нет. Минимальные каталоги: исполнители, группы, песни, релизы (+ уже существующий `/genres`).
- На `/` списков нет (HOME-0). Поиск и фильтры — EPIC-010.

Track остаётся дочерней сущностью Release (уникальный номер на издании) и всегда указывает на Recording. UI записи показывает появления на релизах.

## Stories

Каждая story дополняет controlled seed. STORY-005: публикация Performer по каноническому имени; изображение опционально и в срезе отсутствует; seed Charlie Parker, Count Basie, Benny Goodman, Louis Jordan, Big Joe Turner, Louis Armstrong.

1. [STORY-005: открыть опубликованного исполнителя](story-005-view-published-performer/README.md) — `done`, [#31](https://github.com/K-Mickey/roots-of-rhythm/issues/31).
2. [STORY-006: открыть опубликованную группу](story-006-view-published-group/README.md) — `done`, [#32](https://github.com/K-Mickey/roots-of-rhythm/issues/32).
3. [STORY-007: открыть опубликованную песню](story-007-view-published-song/README.md) — `accepted`, [#33](https://github.com/K-Mickey/roots-of-rhythm/issues/33).
4. [STORY-008: открыть опубликованную запись](story-008-view-published-recording/README.md) — `accepted`, [#34](https://github.com/K-Mickey/roots-of-rhythm/issues/34).
5. [STORY-009: открыть опубликованный релиз](story-009-view-published-release/README.md) — `draft`, [#35](https://github.com/K-Mickey/roots-of-rhythm/issues/35).
6. [STORY-010: показать связанные сущности на Genre](story-010-genre-related-entities/README.md) — `draft`, [#36](https://github.com/K-Mickey/roots-of-rhythm/issues/36).

`tasks.md` появляется после утверждения соответствующей story. STORY-007 и STORY-008 декомпозированы; tracker TASK issues создаются только после отдельного dry run и подтверждения.

## Не включает

- единый поиск и фильтры каталогов (EPIC-010);
- Editorial UI (EPIC-005);
- встроенный плеер и провайдеры (EPIC-009);
- Dance, Story, карта карьеры;
- постоянная Interpretation, обязательное дерево covers, единый `is_original`;
- ReleaseCredit; отдельные session/take/master aggregates;
- автоматическое определение Work, оригинала или жанра по внешним metadata;
- публичная страница Track;
- Style/Scene/Tradition как отдельные public pages.

## Зависимости

- STORY-001/002/004 `done`;
- People Catalog и Music Catalog aggregates ([workshop 004](../../domain/workshops/004-aggregate-boundaries.md));
- ClassificationAssignment, RecordingCredit, GroupMembership, Track.

## История изменений

- 2026-08-19: Product Owner включил страницы Песни и Релиза в EPIC-002; запись всегда к песне; каталог записей не нужен; текст песни на странице; трек связан с записью через join на релизе.
- 2026-08-27: Work определяется авторским произведением; Recording связывается через usages, страница песни получает хронологию и жанровые фасеты, историческое первенство выражается Claims без дерева каверов.
