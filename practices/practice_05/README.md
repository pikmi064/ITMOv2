# Практика 5 — две команды, одна фича

Реализовано редактирование задач в существующем трекере **«После пары»**: название, предмет и срок меняются без удаления задачи и потери отметки выполнения. Использован **GitHub Spec Kit v1.2.4**. Исходные UI/logic спеки подготовлены двумя отдельными агентами, затем согласованы **до кода**.

Задание: [презентация, слайд 16](prenetation.pdf). Прочитаны все 16 слайдов; текстовая и визуальная проверка подтвердили, что ДЗ — «Две команды — одна фича», а не устаревшая строка о третьей User Story в корневом README.

**Начать подготовку к защите:** [ПОЯСНЕНИЕ.md](ПОЯСНЕНИЕ.md).

## Запуск

Python 3.11+ и Node 20+. У приложения нет внешних runtime-зависимостей.

```bash
cd practices/practice_05
make check                    # HTTP, unit, JavaScript syntax
make spec-check               # настоящая проверка структуры Spec Kit
make demo                     # http://127.0.0.1:8050, временная база
```

Для сквозной проверки в чистом окружении:

```bash
npm ci
npx playwright install chromium
make e2e
```

Если Chrome уже установлен, можно использовать `PLAYWRIGHT_CHANNEL=chrome make e2e`. Локальный прогон сделан с bundled Playwright 1.62.1 и Chrome; CI устанавливает Chromium той же закреплённой версии Playwright. Тест запускает собственный сервер на свободном порту и временную SQLite, затем удаляет её.

`make serve` запускает обычное приложение на 8050 с `project/data/tasks.sqlite3` (игнорируется Git). Для защиты предпочтителен `make demo`, чтобы показывать тестовые задачи. Ctrl+C завершает демо.

## Соответствие оцениванию

| Критерий слайда 16 | Баллы | Что предъявить |
|---|---:|---|
| Другой SDD-фреймворк, применение и сравнение | 2 | [.specify](.specify/), [CLI init/version](evidence/spec-kit-init.txt), [сравнение](FRAMEWORK_COMPARISON.md), plan/tasks/spec |
| Две спецификации, согласованные до кода | 2 | [before UI](specs/before/ui.md), [before logic](specs/before/logic.md), [итог UI](specs/001-edit-task/ui.md), [итог logic](specs/001-edit-task/logic.md), [контракт](specs/001-edit-task/contracts/api.md), [два протокола](evidence/ui-agreement.md) |
| Работающие UI и логика, сквозные проверки | 5 | [server](project/server.py), [UI](project/index.html), [HTTP tests](project/tests/test_http.py), [E2E](project/tests/e2e.cjs), [фактические результаты](evidence/browser-results.json), живое демо |
| Рефлексия | 1 | [reflection.md](reflection.md): согласование, трудности, выводы и ограничения |

Сумма критериев — 10. Это карта доказательств, а не гарантия оценки преподавателя. В отчётах не выдуманы действия человека: пользователь делегировал принятие решений агенту.

## Порядок, который можно проверить в Git

1. Baseline — 7 старых тестов, [вывод](evidence/baseline.txt).
2. Два агента независимо создают `specs/before/`, затем сверяют общий контракт. [UI agreement](evidence/ui-agreement.md), [logic agreement](evidence/logic-agreement.md).
3. Коммит **`ca88739`** содержит согласованные спеки/конституцию/план и **не содержит `project/`**. Это проверяемое доказательство «до генерации кода».
4. HTTP-тесты написаны до PUT: [RED](evidence/http-red.txt), затем [GREEN](evidence/http-tests.txt). Это разные фактические запуски.
5. Реализация и [сквозные проверки](evidence/browser-tests.txt): сохранение/reload/restart, отмена, 400/404, Unicode, network failure, блокировка повторного PUT, 200 PUT + GET failure, поиск/фильтр, done/delete, клавиатура/375px.
6. Независимое ревью: [REVIEW.md](REVIEW.md). Итоговая сверка Spec Kit: [CONVERGENCE.md](CONVERGENCE.md).

## Устройство

- `project/` — snapshot небольшого приложения практики 4 + новая фича; предыдущие практики не правились, реальные данные не копировались.
- `specs/001-edit-task/` — итоговые требования, контракт, план, модель данных и задачи.
- `.specify/` и `.agents/skills/speckit-*` — реальные установленные материалы Spec Kit; тексты заполнял агент, CLI создавал структуру.
- `scripts/` и `Makefile` — проверки и безопасное демо.
- `evidence/` — факты запусков и изображения. Полный индекс: [EVIDENCE.md](EVIDENCE.md).
- CI: `.github/workflows/practice05.yml`, запускает структуру, unit/HTTP, JS и Chromium E2E.

Ограничения: локальная однопользовательская программа; при параллельных правках последнее сохранение побеждает. Истории/undo и обнаружения конфликтов нет. Это явно согласованный scope.
