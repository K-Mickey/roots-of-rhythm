# GitHub delivery workflow

Статус: `accepted`.

Дата проверки доступности: 2026-08-17.

## Решение

Использовать GitHub Issues, GitHub Projects и Milestones как operational projection SDD-документов. Для одного разработчика возможностей GitHub Free достаточно: plan стоит 0 USD, поддерживает repositories и базовый code workflow, а Projects предоставляет table, board, roadmap, custom fields, charts и automation: [GitHub pricing](https://github.com/pricing), [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects).

Платные функции и metered products не включать без отдельного решения. Для private repository учитывать месячный лимит GitHub Actions; public repositories получают бесплатные standard Actions minutes: [included usage](https://docs.github.com/en/billing/reference/product-usage-included).

## Источники истины

```text
docs/specs Epic/Story — цель, требования, границы и acceptance criteria
GitHub Issue          — исполняемая работа и её текущее состояние
Pull Request          — изменение и evidence выполненных проверок
Project/Milestone     — поток работы и граница release
```

Issue не становится копией specification. Он содержит краткий результат, ссылку на точный документ/requirement IDs, зависимости, definition of done и проверяемые task-specific details. Изменение продуктового поведения сначала синхронизируется со specification, затем с issue.

## Обязательный bootstrap до кода

1. Убедиться, что project опубликован в GitHub repository и доступна авторизация для создания Issues/Project.
2. Создать один GitHub Project `Swing Music Story`.
3. Настроить status: `Backlog`, `Ready`, `In progress`, `Review`, `Done`; `Blocked` хранить отдельным flag/reason, чтобы не терять основной этап.
4. Добавить поля: `Type`, `Epic/Story`, `Priority`, `Milestone`. Estimates и iterations не добавлять до реальной пользы.
5. Создать milestone первой vertical slice.
6. Создать issues для принятых epics/stories и утверждённых задач декомпозиции; draft/future scope переносить как явно помеченный backlog, не как ready work.
7. Проверить двусторонние ссылки: document -> tracker item и issue -> source specification.
8. Только после этого переводить первую задачу в `Ready` и начинать application code.

Создание внешних tracker items выполняется отдельным шагом после явного подтверждения состава импорта и при наличии авторизованного GitHub connector/CLI. Создание Project не даёт разрешения создавать branches, commits или pull requests.

Для bootstrap и полной сверки использовать навык `sync-github-tracker` или команду `/sync-tracker`. Для добавления задач одной утверждённой декомпозиции использовать `create-tracker-tasks`. Оба workflow обязаны сначала показать dry run и быть идемпотентными.

## Правила потока

- WIP limit для одного разработчика: одна основная issue в `In progress`.
- В `Ready` попадает только работа с закрытыми блокирующими требованиями и понятным definition of done.
- Pull request связывается с issue и specification; required checks должны завершиться до `Done`.
- `Done` означает выполненные acceptance criteria, актуальные документы/контракты и пройденные обязательные проверки, а не только написанный код.
- Blocked item хранит причину, владельца следующего действия и дату повторной проверки.
- Future ideas остаются в docs future scope или backlog и не смешиваются с committed milestone.

## Контроль процесса

Периодически проверять:

- cycle time `In progress -> Done`;
- возраст blocked items;
- escaped defects;
- незапланированную работу;
- scope changes после принятия story;
- прохождение acceptance criteria и CI.

Story points, количество commits и объём кода не используются как метрики продуктивности.

## Интеграция с SDD workflow

```text
идея
  -> sync-spec / epic / story
  -> утверждение
  -> decompose-story
  -> create-tracker-tasks
  -> реализация
  -> проверки и review
```

При расхождении tracker и repository действует приоритет источников из `AGENTS.md`; GitHub Project показывает состояние работы, но не переопределяет принятую specification.
