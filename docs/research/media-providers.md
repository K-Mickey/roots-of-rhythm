# Исследование музыкальных провайдеров

Статус: `research`

Дата исследования: 2026-08-15.

Решение о провайдерах пока не принято.

## Требования

- доступность для значимой части пользователей в РФ;
- официальный способ embed или внешней ссылки;
- отсутствие собственного хранения аудио;
- возможность связать конкретную Recording с контентом провайдера;
- graceful fallback при блокировке, удалении или региональной недоступности;
- отсутствие обязательной авторизации посетителя для чтения страницы;
- соблюдение branding и platform terms.

## Spotify

Официально предоставляет embeds для track, album, artist и playlist, а также iframe/oEmbed API. Это технически зрелый вариант, но пользовательская доступность в РФ ограничивает его как единственный provider. Источник: [Spotify Embeds](https://developer.spotify.com/documentation/embeds).

Вывод: поддерживать как один из providers, но не делать обязательным и единственным.

## Yandex Music

В официальных материалах найдено разрешённое использование ссылок и фирменного badge, ведущего на song, album или artist. Публичная официальная документация полноценного Music API или поддерживаемого универсального embed для сторонних сайтов не найдена. Неофициальные библиотеки используют внутренние endpoints и не подходят как стабильная основа продукта. Источник: [визуальные элементы Яндекс Музыки](https://yandex.ru/support/music/ru/performers-and-copyright-holders/visual).

Вывод: для MVP безопасно поддержать внешнюю ссылку и корректный badge после проверки применимости правил. Embed и metadata API считать `unsupported` до письменного подтверждения или официальной документации. Не использовать неофициальный API с пользовательскими токенами.

## YouTube

Официальный IFrame Player API позволяет встраивать и управлять видео. Для старых записей часто доступны официальные label/artist uploads, но наличие и доступность конкретного видео нестабильны; также это видеоплатформа, а не канонический каталог записей. Источник: [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference).

Вывод: хороший второй embed-provider при ручном выборе редактором конкретного официального или правомерного видео. Не выполнять автоматический поиск и выбор первого результата.

## SoundCloud

SoundCloud предоставляет настраиваемый embedded player, Widget API и oEmbed. Каталог исторического jazz/swing может быть неполным, а API usage регулируется отдельными условиями. Источники: [SoundCloud Developers](https://developers.soundcloud.com/) и [SoundCloud Public APIs](https://help.soundcloud.com/hc/en-us/articles/115003446727-SoundCloud-public-APIs).

Вывод: технически пригоден как дополнительный provider, но не гарантирует покрытие нужного каталога.

## Bandcamp

Предоставляет официальный embedded player для доступных на Bandcamp tracks и albums. Покрытие ранней исторической музыки, вероятно, недостаточно для основного провайдера. Источник: [Bandcamp embedded player](https://get.bandcamp.help/en/articles/15263071-how-do-i-create-a-bandcamp-embedded-player).

Вывод: дополнительный provider для более поздней и независимой музыки.

## MusicBrainz

Не является проигрывателем, но подходит как нейтральный идентификатор и источник базовых metadata о artists, recordings, releases, works и внешних relationships. Источник: [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API).

Вывод: рассмотреть как metadata/reconciliation provider независимо от playback providers.

## Рекомендация для proof of concept

Не выбирать «главный проигрыватель». Реализовать provider-neutral модель и два различных способа представления:

1. Spotify embed, когда он доступен.
2. Yandex Music external link/badge для доступности пользователям РФ.
3. Опционально YouTube embed как второй реально воспроизводимый provider после проверки конкретного контента.

Таким образом, продукт проверит одновременно embed и link-only сценарии. Финальный набор определить после прототипа на 20–30 записях из стартового каталога.

## Предлагаемая модель

```text
MediaReference
├── id
├── recording_id
├── provider_key
├── external_id optional
├── canonical_url
├── presentation: embed | external_link
├── embed_url optional
├── region_notes optional
├── availability_status
├── verified_at
└── editorial_status
```

Provider хранится как конфигурируемый ключ и adapter, а не как обязательные nullable-колонки `spotify_id`, `yandex_id`, `youtube_id` в Recording.

Frontend получает список доступных представлений и не содержит доменной логики выбора провайдера.

## Proof-of-concept checklist

- выбрать 20–30 стартовых Recording;
- измерить покрытие Spotify, Yandex Music, YouTube и SoundCloud;
- проверить доступность из целевых регионов;
- проверить официальный embed/link flow и branding requirements;
- проверить поведение удалённого и region-locked контента;
- проверить mobile и desktop;
- зафиксировать решение отдельным ADR.
