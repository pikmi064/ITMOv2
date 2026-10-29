# GitHub Spec Kit и OpenSpec

Использован реальный GitHub Spec Kit **v1.2.4**, официальный tag и исходный commit `43486672fe826d230d884815be7cc2026469a6ba`. [Документация выбранной версии](https://github.com/github/spec-kit/tree/v1.2.4/docs), [OpenSpec 1.14.1 — версия из презентации](https://github.com/Fission-AI/OpenSpec/tree/v1.14.1). Сравнение OpenSpec опирается на полный материал слайдов 1–15; его CLI здесь не запускался. Статус современного OpenSpec не предполагается.

| Аспект | OpenSpec на практике 5 | Spec Kit в этой работе |
|---|---|---|
| Начало | explore существующего кода и baseline | исследование server/index/tests, baseline 7/7, конституция |
| Требования | proposal + specs в change | spec.md + две независимые UI/logic спеки |
| Уточнение | update change после review | общий contracts/api.md и два протокола сверки |
| Проектные правила | config.yaml, rules для будущих артефактов | .specify/memory/constitution.md, шаблоны и команды |
| План реализации | design + tasks | plan.md, research.md, data-model.md, tasks.md |
| Проверки | validate проверяет документы, runner поведение | check-prerequisites проверяет структуру; unittest/Playwright — поведение |
| Завершение | sync main specs → archive change | converge проверяет текущий код против spec/plan/tasks; итог — Git commits и PR |

Сгенерированные материалы Spec Kit сохранены с [исходной MIT-лицензией](SPEC_KIT_LICENSE).

## Что действительно применено

`specify init` создал реальные `.specify/` и `.agents/skills/speckit-*` из bundled assets. Template resolver разрешил constitution/spec шаблоны; `setup-plan.sh` и `setup-tasks.sh` создали основы документов, которые агент заполнил. `check-prerequisites.sh` обнаружил документы фичи. Фактические выводы лежат в `evidence/spec-kit-*`, `setup-plan.json`, `setup-tasks.json`. Указатель активной фичи локальный и по правилам фреймворка не коммитится: воспроизводимый `make spec-check` явно передаёт `SPECIFY_FEATURE_DIRECTORY`.

Порядок работы соответствует SDD: constitution → specify двух команд → clarify контракта → plan → tasks → implement → converge. CLI ничего не генерирует через LLM: спецификации/код написал агент, каркас и проверки структуры исполнил CLI. Мы читали установленные инструкции и применяли их в текущем агентском сеансе, а не выдавали имена slash-команд за shell-вызовы.

## Практический вывод

Для этой маленькой brownfield-фичи OpenSpec даёт более короткий change-цикл и явное обновление текущих specs после приёмки. Spec Kit добавляет больше документов и конституцию, зато удобно разделяет цель, технический план и исполняемые задачи. Сам по себе набор шаблонов согласованности не гарантирует: её дали сверка двух независимых draft, единый контракт и проверки поведения.
