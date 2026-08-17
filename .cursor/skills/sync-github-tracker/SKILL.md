---
name: sync-github-tracker
description: Синхронизировать SDD-документы проекта с GitHub Issues, Projects и Milestones. Использовать при просьбе подключить, первоначально заполнить, импортировать, сверить или повторно синхронизировать GitHub tracker. Не декомпозировать требования и не выполнять внешние записи без dry run, явного подтверждения и авторизованного GitHub-инструмента.
---

# Sync GitHub tracker

1. Прочитать `docs/roadmap/delivery-workflow.md`, `docs/specs/epic-map.md` и выбранные исходные specifications/decompositions.
2. Проверить target repository, GitHub Project, доступную авторизацию и область синхронизации. Если target неоднозначен, не выполнять внешние записи.
3. Read-only получить существующие issues, project items, labels и milestones. Сопоставлять по стабильному идентификатору требования и ссылке на source document, а не только по заголовку.
4. Подготовить inventory с категориями `create`, `update`, `no-op`, `conflict`, `skip`. Draft/future scope помещать только в явно помеченный backlog; не переводить его в `Ready`.
5. Показать dry run: target, создаваемые и обновляемые объекты, статусы, зависимости, конфликты и local write-back. Не скрывать частичную синхронизацию.
6. Получить явное подтверждение именно показанного batch. Изменение scope после preview требует нового подтверждения.
7. Выполнить записи через авторизованный GitHub connector/CLI. Создавать issues идемпотентно; добавлять их в Project и Milestone только по подтверждённому mapping.
8. После успешной внешней записи добавить или обновить tracker links в source documents, не меняя требования и статусы документов.
9. Повторно прочитать затронутые GitHub objects и проверить IDs, URLs, Project/Milestone membership и отсутствие дублей. Вернуть отчёт `created/updated/no-op/conflict/failed`.

## Ограничения

- Не закрывать, не удалять, не архивировать и не перемещать существующие items без отдельной явной команды.
- Не перезаписывать ручные изменения при расхождении tracker и specification; отметить `conflict` и остановить этот item.
- Не создавать task issue без утверждённой декомпозиции. Epic/story/future backlog синхронизировать с сохранением документированного статуса.
- Не создавать branches, commits, pull requests, releases и application code.
- Не записывать secrets, access tokens и чувствительные данные в issue bodies, logs или документы.
- Specification остаётся источником продуктового поведения; tracker отражает исполняемую работу.
