# Исследование источников музыкальной классификации

Статус: `research`

Дата проверки: 2026-08-15.

## Вопрос

Можно ли заимствовать из Wikipedia, Wikidata и MusicBrainz готовое различение Genre, Style, Scene и Tradition и автоматически использовать его как доменную классификацию?

## Наблюдения

### MusicBrainz

- Genre поддерживается как часть tag system: только теги из отдельного списка показываются как жанры. Жанровые назначения субъективны, пользователи могут голосовать за них и против них. Источник: [MusicBrainz Genre](https://musicbrainz.org/doc/Genre).
- API позволяет получать жанры для музыкальных сущностей, включая Artist, Recording, Release Group и Work. Это подтверждает, что несколько классификаций могут относиться не только к исполнителю или альбому, но и к конкретной Recording или MusicalWork. Источник: [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API).
- MusicBrainz различает Work, Recording, Release Group и Release и поддерживает отдельные отношения и credits. Даты отношений могут быть неполными или отсутствовать. Источники: [MusicBrainz database](https://musicbrainz.org/doc/MusicBrainz_Database), [MusicBrainz relationships](https://musicbrainz.org/doc/Relationships).

### Wikidata и Wikipedia

- Свойство Wikidata `genre (P136)` применяется к произведениям и исполнителям, но среди допустимых значений объединяет genre, musical style и близкие категории. Источник: [Wikidata genre (P136)](https://www.wikidata.org/wiki/Property:P136).
- Свойство `movement (P135)` также широко: оно охватывает movement, scene, school, trend и art style. Оно не даёт готового строгого различения Scene, Style и Tradition. Источник: [Wikidata movement (P135)](https://www.wikidata.org/wiki/Property:P135).
- Wikipedia полезна как начальная историческая навигация и источник формулировок и ссылок, но её текст и инфобоксы сами по себе не образуют стабильную единую таксономию. Это вывод из различий между структурой Wikidata и нужным проекту ubiquitous language, а не утверждение самой Wikipedia.

## Вывод

Источников достаточно, чтобы:

- импортировать кандидатов Genre и Style;
- назначать несколько классификаций Group, Release, Recording и MusicalWork;
- сохранять внешний идентификатор, исходный label и provenance;
- создавать Claims о Scene и Tradition из исторического текста.

Источников недостаточно, чтобы без редакционной нормализации:

- автоматически отличать Genre от Style;
- считать сочетание места и периода самостоятельной Scene;
- выделять Tradition по единому внешнему словарю;
- переносить пользовательский tag в доменную истину.

Рекомендуемая политика: источник предлагает `ClassificationCandidate`, редактор связывает его с существующим понятием, создаёт новое понятие по утверждённым правилам либо оставляет термин только в Claim. Автоматический импорт не публикует классификацию.

