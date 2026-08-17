# Исследование Genre relations первого seed

Статус: `research`

Дата проверки: 2026-08-16.

Продуктовое решение: оба предложенных Claims и институциональные Smithsonian/Library of Congress Evidence подтверждены Product Owner 2026-08-16 для seed STORY-001.

Цель: предложить исторически обоснованные relations между Jazz, Swing и Jump Blues для STORY-001. Исследование не публикует Claims автоматически: формулировки и Evidence должны пройти редакционное подтверждение.

## Состав seed

- Jazz;
- Swing;
- Jump Blues.

Это минимальный связный фрагмент, а не окончательная таксономия и не полный набор 6–10 Genre MVP.

## Кандидат 1: Swing developed_from Jazz

### Предлагаемая структура

```text
subject: Swing
relation_type: developed_from
target: Jazz
temporal_context: late 1920s–1930s, approximate
geographic_context: United States
evidence_status: supported after editorial review
```

### Предлагаемое explanation

Swing сформировался внутри американской джазовой традиции на основе развития оркестровых аранжировок, ритмической организации и роли импровизирующих солистов. В 1930-е эти изменения оформились в Swing Era и сделали большие джазовые оркестры центральной частью массовой танцевальной культуры.

### Почему `developed_from`

Smithsonian описывает смену Jazz Age на Swing Era внутри одной истории Jazz, связывая её с big bands, аранжировками Fletcher Henderson, Benny Goodman и более текучим ритмом Count Basie. Это сильнее простого внешнего `influenced`: Swing рассматривается как историческое развитие внутри Jazz.

Направление соответствует принятому enum: более новый Swing указывает на предшественника Jazz.

### Почему не другие relation types

- `influenced` слишком слаб и не выражает внутреннюю преемственность;
- `contributed_to_emergence_of` допустим формально, но хуже показывает, что Jazz является не одним случайным входом, а основной традицией;
- `overlaps_with` описывает размытые границы, но не историческое происхождение.

### Evidence candidates

1. [Smithsonian Music — Jazz: An Introduction to the History and Legends Behind America's Music](https://music.si.edu/story/jazz): Jazz Age переходит в Swing Era; названы big-band development, Henderson/Goodman и Basie.
2. [Smithsonian Music — Jazz and Blues](https://music.si.edu/spotlight/african-american-music/jazz-blues): 1920-е описаны как Jazz era, а 1930-е — как приход Swing Era с Ellington и другими big bands.

## Кандидат 2: Swing contributed_to_emergence_of Jump Blues

### Предлагаемая структура

```text
subject: Swing
relation_type: contributed_to_emergence_of
target: Jump Blues
temporal_context: late 1930s–1940s, approximate
geographic_context: United States urban African American music scenes
evidence_status: supported after editorial review
```

### Предлагаемое explanation

Swing был одним из основных входов в формирование Jump Blues. Музыканты перенесли swing-ритм, духовые riffs и опыт больших оркестров в более компактные составы, соединив их с Blues, shuffle rhythm и Boogie-Woogie bass lines. Поэтому Jump Blues нельзя описывать как продолжение только одного Swing.

### Почему `contributed_to_emergence_of`

Smithsonian называет Jump Blues важным прототипом Rhythm and Blues и описывает музыку Louis Jordan как соединение элементов Swing и Blues с shuffle, Boogie-Woogie bass и короткими духовыми riffs. Swing является причинно значимым источником, но не единственным предшественником.

### Почему не `developed_from`

`Jump Blues developed_from Swing` создаёт слишком линейную картину и недооценивает Blues и Boogie-Woogie. Принятый `contributed_to_emergence_of` специально предназначен для одного из нескольких источников формирования.

### Evidence candidates

1. [Smithsonian Center for Folklife and Cultural Heritage — Tell It Like It Is: A History of Rhythm and Blues](https://folklife.si.edu/magazine/freedom-sounds-tell-it-like-it-is-a-history-of-rhythm-and-blues): Jump Blues Louis Jordan описан как смесь Swing и Blues; перечислены shuffle, Boogie-Woogie bass lines и riffs.
2. [Smithsonian Folkways — Rhythm and Blues program article](https://folklife-media.si.edu/docs/festival/program-book-articles/FESTBK2011_05.pdf): печатная версия того же исторического контекста и музыкальных признаков.
3. [Library of Congress — Rhythm and Blues](https://www.loc.gov/collections/songs-of-america/articles-and-essays/musical-styles/popular-songs-of-the-day/rhythm-and-blues/): ранний R&B связывается с African American Swing, Jazz и Blues, а послевоенные small groups противопоставляются Swing orchestras по размеру и rhythmic drive.

## Почему не добавляем Jazz ↔ Jump Blues напрямую

Источники подтверждают Jazz-компонент Jump Blues, но первый seed уже выражает проверяемую цепочку через Swing. Отдельная прямая relation без нового explanation может дублировать тот же аспект. Она добавляется только если content research покажет самостоятельное влияние Jazz, не сводимое к Swing.

## Ограничения исследования

- `Jazz` является широким Genre; explanation не должен создавать впечатление одного линейного родителя для всех форм Swing.
- `Swing` одновременно употребляется как Genre, эпоха и ритмическая практика. Seed Claim относится к Genre, а explanation обязано удерживать этот смысл.
- Временные и географические границы пока приблизительны; перед публикацией их нужно представить структурой, поддерживающей приблизительность, без ложной точности.
- Институциональный источник является Evidence candidate, но получает `supported` только после редакционного review конкретного фрагмента и формулировки Claim.

## Рекомендация

Включить в seed два Claims:

1. `Swing developed_from Jazz`;
2. `Swing contributed_to_emergence_of Jump Blues`.

Не добавлять `overlaps_with` только ради проверки симметричного enum. Его поведение проверяется контрактом и тестовыми fixtures, а published seed содержит только нужные исторические связи.

## Перед data contract

- Решить, как представить приблизительные temporal/geographic contexts без свободных фиктивных значений.
