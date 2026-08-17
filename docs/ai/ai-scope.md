# RAG, MCP и агенты

Статус: `draft`

AI-возможности входят в учебную и продуктовую цель MVP, но строятся поверх работающего каталога, источников и editorial workflow.

## RAG

### Цель первой версии

Пользователь задаёт вопрос об опубликованной области от swing до раннего rock and roll и получает:

- краткий структурированный ответ;
- ссылки на использованные источники;
- указание связанных сущностей;
- явное сообщение, если корпус не подтверждает ответ;
- отделение подтверждённого от спорного.

### Данные RAG и их владельцы

```text
Historical Knowledge                 AI Research
Source                               IngestionJob
└── SourceVersion[]                  RetrievalChunk
      └── SourceFragment[] ────────→ EmbeddingRecord / IndexEntry
            └── ClaimEvidence[]      CorpusAdmission
                                     RetrievalRun / EvaluationRun
                                     AgentRun / AIProposal
```

Historical Knowledge владеет Source, версиями, фрагментами и Evidence как provenance независимо от способа поиска. AI Research владеет только техническими и перестраиваемыми представлениями: chunk для конкретной модели, embedding, индекс, запуск и proposal. Точная граница описана в [supporting capabilities](../domain/supporting-capabilities.md).

### Что публично

Для опубликованного Claim всегда публичен evidence status. Для `supported` Claim публичны как минимум citation metadata и locator: URL, автор, название, издатель, дата, страница или раздел. `unverified` не изображается подтверждённым и не получает фиктивную citation.

Текст SourceFragment по умолчанию является внутренним системным материалом. Показывать полный фрагмент или цитату можно только когда это разрешает лицензия и политика конкретного источника. Embeddings, технические chunks и ingestion metadata не являются публичным контентом.

Для открыто лицензированных источников может быть разрешено публичное отображение фрагментов с атрибуцией. Для защищённых книг система может хранить metadata, locator и внутреннее извлечение в объёме, отдельно согласованном после правового исследования.

### Ingestion workflow

```text
register source → verify rights/access → extract → segment
→ index → retrieve test → editorial approval for corpus
```

Добавление документа в хранилище не означает автоматического включения в публичный RAG.

В фактический retrieval-корпус первой версии входят только опубликованные `supported` Claims и одобренные SourceFragments. `unverified` исключаются из основания ответа. `disputed` могут использоваться только в режиме явного представления разногласий с цитатами для каждой позиции.

### Evaluation

До релиза подготовить небольшой набор эталонных вопросов:

- вопросы с прямым ответом;
- вопросы, требующие нескольких источников;
- спорные вопросы;
- вопросы вне корпуса;
- вопросы с похожими именами исполнителей и записей.

Проверять groundedness, корректность citations, полноту и правильный отказ.

## MCP

MCP — не набор обычных пользовательских REST-endpoints. Это отдельная протокольная граница, через которую AI-клиенты обнаруживают и вызывают resources, tools и prompts. Сервер может переиспользовать те же application use cases, что HTTP API, но имеет отдельные transport, schemas, authentication и authorization.

Официальная архитектура MCP использует host–client–server и позволяет серверу публиковать tools, resources и prompts. Для локального прототипа подходит stdio, для удалённого сервера — Streamable HTTP. См. [MCP architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture) и [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).

### Read-only MCP MVP

Tools:

```text
search_entities(query, types, filters)
get_entity(type, id)
get_related_entities(type, id, relation_types)
get_claims(subject, status=published)
get_sources(entity_or_claim)
ask_published_corpus(question)
```

Resources:

```text
music://genres/{id}
music://performers/{person_id}
music://groups/{id}
music://dances/{id}
music://recordings/{id}
music://stories/{id}
```

Общий resource `artists` не используется: Person в роли Performer и Group имеют разные identity и владельцев правил.

### Редакторский MCP позднее

```text
create_draft_claim
attach_source
suggest_entity_match
submit_for_review
```

Write-tool всегда:

- требует аутентифицированного Editor;
- проверяет authorization в application layer;
- создаёт draft;
- аудитируется;
- не публикует автоматически;
- возвращает созданный идентификатор и результат валидации.

## Агенты

Планируемые роли:

- Researcher извлекает кандидаты Claims из разрешённых источников.
- Critic проверяет, действительно ли evidence подтверждает формулировку, ищет противоречия.
- Editor assistant нормализует структуру и предлагает связи с существующими сущностями.
- Human Editor принимает, исправляет или отклоняет.
- Publisher выполняет детерминированный переход утверждённого материала в published.

```text
Source → Researcher → AI Proposal/Draft → Critic → Human Editor → Published
```

Agent workflow добавляется после ручной реализации того же процесса. Иначе невозможно определить корректные tools, инварианты и evaluation.

## Архитектурная граница

REST/HTML, RAG, MCP и агенты вызывают общие application use cases. Они не обращаются напрямую к таблицам и не дублируют правила публикации:

```text
Web UI ──┐
REST API ├── Application use cases ── Domain ── Ports
MCP ─────┤
Agents ──┘
```
