# Research

Исходник: origin/main 9156eac, project практики 4. В базе уже есть id/title/subject/deadline/done; GET сортирует done, пустой срок в конце, deadline, id DESC. PATCH принимает done, POST валидирует строки/каноническую дату, UI имеет поиск/фильтры и безопасный textContent.

Решение: PUT полного редактируемого подмножества вместо PATCH. Причина: не смешивать отметку выполнения и редактирование. Ответ с записью нужен для нормализации и различения PUT success/GET failure. Native dialog даёт модальность и управление Tab без новой библиотеки. Сервер получает --database ради безопасных демонстраций; default остаётся локальным data/tasks.sqlite3 внутри нового snapshot.

Spec Kit v1.2.4 установлен из официального tag (commit 43486672fe826d230d884815be7cc2026469a6ba). Применены реальные init, template resolver, setup-plan/setup-tasks/check-prerequisites. Тексты артефактов и код пишет агент, а не CLI. Источники: https://github.com/github/spec-kit/tree/v1.2.4 и docs/quickstart.md этого tag.
