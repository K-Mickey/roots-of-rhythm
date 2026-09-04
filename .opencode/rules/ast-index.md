# ast-index

> Структурный AST-поиск по коду: индексирует символы, ссылки, импорты и вызовы в SQLite. Экономит контекст агента, заменяя чтение больших файлов структурными срезами.

## Хронология индекса

- После `git pull`, переключения ветки или rebase запускать `ast-index update` — инкрементально переиндексирует только изменённые файлы.
- После добавления/удаления исходных корней — `ast-index rebuild`.

## Обязательные правила поиска

1. Для любого поиска по коду **сначала** использовать `ast-index`.
2. **Не дублировать результат** — если ast-index вернул совпадения, это и есть ответ; не перепроверять grep-ом.
3. Использовать Grep **только** если ast-index ничего не вернул, или для строковых/регекс-паттернов, не являющихся именами символов.

## Обязательные правила чтения

1. **Перед `Read` файла длиннее 500 строк** запускать `ast-index outline <file>`.
2. По outline определить нужный символ/диапазон строк, затем читать только этот срез через `offset` / `limit`.
3. Never bulk-read большие файлы целиком — это тратит контекст и ухудшает ответы.

## Правила для субагентов

Субагент (Task/Agent) не наследует этот файл. Включать блок ниже в промпт субагента:

```
Use `ast-index` via Bash for code search (NOT grep / the Grep tool):
  ast-index explore "how does X work" — one-shot context: ranked source + neighbours + tests (--rwr for graph)
  ast-index search "query"           — universal search
  ast-index file "Name"              — find a file by name fragment
  ast-index symbol "Name"            — find a symbol definition
  ast-index class "Name"             — find a class / interface / struct
  ast-index usages "Name"            — every usage of a symbol
  ast-index callers "func"           — functions that call this one
  ast-index implementations "Iface"  — concrete implementers of an interface
  ast-index refs "Name"              — cross-references (defs + imports + usages)
Use Grep ONLY if ast-index returned empty.

Before Read-ing any file over 500 lines, FIRST run
  ast-index outline <file>
to get its structure, then Read only the targeted slice via offset/limit.
Never bulk-read large files.
```

## Шпаргалка команд

Подробный список и флаги: `ast-index --help`.

- **Поиск:** `search`, `file`, `symbol`, `class`
- **Использования и поток:** `usages`, `callers`, `call-tree`, `refs`
- **Иерархия:** `implementations`, `hierarchy`, `extensions`
- **Модули и зависимости:** `module`, `deps`, `dependents`, `api`, `unused-deps`
- **Файлы:** `outline`, `imports`, `changed`
- **Качество:** `todo`, `deprecated`, `unused-symbols`
- **Индекс:** `rebuild`, `update`, `stats`

## Типовые сценарии

- `ast-index usages "UserRepository"` — все места использования класса/функции (включая тесты).
- `ast-index implementations "Protocol"` — конкретные реализации интерфейса / ABC.
- `ast-index callers "register_user"` — кто вызывает функцию, без шума строк определения.
- `ast-index deps "."` / `ast-index module ...` — зависимости модуля (Python, Go, TS).
- `ast-index changed` — файлы, изменённые на текущей ветке относительно `origin/HEAD`.
- `ast-index outline backend/app/main.py` — структура файла перед чтением.
- `ast-index todo` — все TODO / FIXME / HACK комментарии.

## Область поиска

Символьные команды поддерживают фильтры:

```bash
ast-index usages "Settings" --in-file config.py   # только в одном файле
ast-index symbol "User" --type class              # только символы-классы
```

## Когда ast-index пуст

Легитимные причины:

- Символ реально не существует в кодовой базе.
- Индекс устарел — запустить `ast-index update` и повторить.
- Символ за макросом / препроцессором (ast-index не раскрывает макросы) — fallback на Grep.
- Ищется строковый литерал, а не символ — использовать Grep.

Не переходить к чтению файлов целиком — использовать Grep с конкретным паттерном.