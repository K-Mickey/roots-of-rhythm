# Media Management, файлы и streaming integrations

Статус: `accepted`

Цель: определить единый край монолита для управляемых binary assets и внешних способов воспроизведения, не создавая отдельный service или bounded context на старте. Проект не хранит и не раздаёт музыкальное аудио.

## Предлагаемая логическая граница

`Media Management` — supporting capability внутри модульного монолита. Он владеет:

- MediaAssetId и identity материала;
- provenance, rights/license и attribution;
- alt text и editorial status;
- storage key оригинала;
- описанием доступных производных вариантов;
- связью использования MediaAsset с объектом через стабильный target ID и роль.
- MediaReference для внешнего streaming provider: provider key, external ID/URL, embed capability, доступность, территориальные ограничения и время проверки.

People, Music, Dance и Historical Knowledge не хранят binary bytes или публичный URL как часть своих aggregates. Они ссылаются на MediaAssetId и определяют предметный смысл использования: например, primary portrait Performer или illustration Story.

Media Management не владеет Person, Genre, Dance, Story, Recording или музыкальной классификацией и не принимает решение, какое изображение исторически корректно. Music Catalog владеет Recording и canonical external identifiers вроде MusicBrainz; Media Management владеет только ссылками на способы внешнего прослушивания этой Recording. Редакторское решение проходит обычный Editorial workflow.

Разрешённый файл Source может физически храниться через Media Management, но Source, SourceVersion, rights interpretation и provenance остаются Historical Knowledge. Media boundary получает только непрозрачный storage key и операционную access/retention policy.

## Размещение на старте

В первой реализации capability находится в том же приложении и deployment unit, но на инфраструктурном краю:

```text
Application use case
  → BinaryObjectStore port
  → local/S3-compatible adapter

Application use case
  → ImageVariantGenerator port
  → in-process image adapter

Application use case
  → StreamingProviderGateway port
  → provider adapter
```

Порты выражают потребность приложения и не копируют API конкретного S3 SDK, image library или streaming provider. Domain objects не импортируют файловую систему, SDK, HTTP client или формат задания worker.

Внутри монолита callers вызывают Media application use cases напрямую. HTTP, RPC, сериализация сетевых DTO и искусственные timeout/retry между внутренними модулями не имитируются.

Отдельный job dispatcher не вводится, пока обработка выполняется синхронно или вручную. Когда thumbnails перестают укладываться в пользовательский запрос, тот же use case вызывается worker-процессом из этого же codebase.

## Будущее выделение

Последовательность:

1. in-process adapter внутри монолита;
2. отдельный worker process с теми же application contracts;
3. task queue при необходимости retries, backpressure или нескольких workers;
4. единый Media Service при независимых нагрузке, failure isolation, lifecycle и ownership данных.

Переход между шагами не меняет MediaAssetId и предметные ссылки. Он меняет execution и delivery semantics, которые принимаются отдельным ADR.

## Инварианты границы

- metadata и binary object не считаются успешно созданными, пока use case не может безопасно повторить или компенсировать незавершённый шаг;
- производный thumbnail перестраиваем и не является источником истины;
- удаление original запрещено, пока существуют разрешённые использования или retention requirement;
- публичная выдача соблюдает rights/access policy;
- adapter не меняет editorial status самостоятельно.

## Не создаём сейчас

- отдельный repository или deployment;
- CDN abstraction;
- универсальный media workflow;
- очередь и event bus;
- видео- и аудиотранскодирование;
- хранение или раздачу музыкального аудио;
- отдельный service для streaming integrations;
- автоматическую модерацию прав.

## Принятые решения

1. Media Management является supporting capability внутри монолита, а не Music Catalog или отдельным bounded context.
2. MediaAsset и MediaReference централизованы; доменные contexts ссылаются на MediaAssetId или запрашивают playback references по RecordingId.
3. Storage, image processing и streaming provider adapters находятся за портами на краю монолита; внутренние callers используют прямые application-вызовы.
4. В будущем эти обязанности выделяются вместе в один Media Service; worker и очередь добавляются только по триггеру.

Решения приняты пользователем 2026-08-15.
