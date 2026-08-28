# UI contract: запись и исполнения на странице песни

Статус: `accepted`

Story: [STORY-008](README.md).  
Базовая Song page: [UI STORY-007](../story-007-view-published-song/ui.md).

## Страница `/recordings/{id}`

Единственный `h1` — title Recording. Если данные есть, показываются:

- Work usages как ссылки на `/songs/{id}` с типом partial/medley, когда он не `complete`;
- primary и дополнительные Person/Group credits;
- дата или период записи, first release date и ISRC;
- жанры Recording;
- фактически звучащие LyricsVersion и доступные reading translations;
- supported origin badges с точными формулировками;
- ListeningGuide.

Пустые опциональные секции скрыты. Нельзя показывать общий badge «Оригинал».

## Каталог `/recordings`

Header содержит ссылку «Записи». Каталог показывает title Recording как ссылку на detail page, опубликованные primary Person/Group, известный период записи и опубликованные Genre. Recording без публичного primary target не показывается; период и Genre могут отсутствовать. Порядок алфавитный по title, затем primary credits. Pagination, поиск и фильтры не добавляются для текущего controlled corpus.

## Расширение `/songs/{id}`

Шапка, авторы, классификация Work и WorkRelation из STORY-007 остаются постоянными.

### Нет Recording

Правая колонка и «Жанры исполнений» скрыты. Страница работает как STORY-007.

### Одна Recording

Recording выбрана автоматически и показана в центральной области. Правая колонка не рендерится.

### Несколько Recording

- Центральная область показывает выбранную Recording.
- Справа находится «Хронология известных записей».
- Элемент различается title, primary credits и известным годом; supported origin badges дополняют, но не заменяют эти данные.
- Список группируется визуально по primary Person/Group без создания отдельной доменной сущности.
- Выбор обновляет `recording` и центральную область без полной перезагрузки.
- На узком viewport список становится горизонтальным блоком над содержимым.

### Жанровые фасеты

Над хронологией показывается «Жанры исполнений»: имя Genre и количество Recording. Выбор `genre` фильтрует список и не меняет секцию «Классификация произведения». Активный facet имеет доступное выбранное состояние; очистка возвращает всю хронологию.

Если текущая Recording не входит в выбранный facet, выбирается первая Recording отфильтрованной хронологии. Пустой результат невозможен для facet, полученного из текущего overview.

### Тексты и языки

В центральной области горизонтально показаны фактически звучащие LyricsVersion выбранной Recording и их reading translations. Выбор обновляет `text` без reload. Одинаковые language tags различаются label; machine translation явно маркируется.

Если точный текст Recording неизвестен, показывается первая опубликованная LyricsVersion Work и сообщение «Соответствие текста этой записи не подтверждено».

### URL и доступность

- `recording`, `genre` и `text` отражают выбранное состояние и работают с back/forward.
- Ссылка из Performer/Group или Genre может передать `recording` и открыть релевантный контекст.
- Invalid/unpublished IDs игнорируются без утечки данных.
- Все controls доступны с клавиатуры, имеют видимый focus и объявляют выбранное состояние.
- SSR выдаёт содержимое безопасного начального состояния; client navigation не заменяет первый render пустым shell.

## Не входит

Плеер, Session/Take/Master UI, дерево covers, автоматическое определение оригинала, обязательные Recording relations и pagination.
