# Как показать практику 4

Все команды выполняются из `practices/practice_04/project`.

Полный реестр выполненных проверок с результатами и исходными доказательствами: [EVIDENCE.md](EVIDENCE.md).

## Что подключено и зачем

| Компонент | Назначение | Файл |
|---|---|---|
| Правила | Границы изменений, команды, работа с данными | [AGENTS.md](AGENTS.md) |
| Playwright skill | Проверка формы и списка через браузер | [.agents/skills/playwright/SKILL.md](.agents/skills/playwright/SKILL.md) |
| Context7 skill | Порядок запроса документации библиотеки | [.agents/skills/context7-mcp/SKILL.md](.agents/skills/context7-mcp/SKILL.md) |
| Context7 MCP | Поиск библиотеки и получение документации | [opencode.json](opencode.json) |
| Собственный MCP | Реальные сроки учебных задач | [mcp_server.py](mcp_server.py), [deadlines.py](deadlines.py) |
| Hook | Запуск проверок после правки инструментом | [.opencode/plugins/check.js](.opencode/plugins/check.js) |
| Runner | Синтаксис Python/JS и семь проверок логики | [scripts/check.py](scripts/check.py), [tests/test_project.py](tests/test_project.py) |

## Подготовка

```bash
make setup
make check
make serve
```

В другом терминале из этой же папки:

```bash
opencode mcp list
opencode
```

Конфиг рассчитан на OpenCode 1.18.31. Модель — `vsellm/anthropic/claude-sonnet-5.5` из существующего пользовательского подключения; секреты в репозиторий не копируются. На другом компьютере нужен собственный провайдер и доступная модель. Ollama и агент практики 3 для этого задания не нужны. Переход на OpenCode 2 требует адаптации hook API.

## Собственный MCP

1. В браузере <http://127.0.0.1:8040> добавьте задачу с ближайшим сроком.
2. Попросите OpenCode: «Прочитай AGENTS.md и вызови study_tracker_get_deadlines с days=7. Что нужно сдать в ближайшие дни?»
3. Попросите вызвать тот же tool с `days=-1`; ожидается ошибка валидации.

В tool один параметр `days`: целое число от 0 до 365. Даты от сегодняшней до сегодняшней плюс N дней включены, просроченные задачи вынесены в отдельный список. Завершённые задачи и задачи без срока не возвращаются. SQLite открывается только для чтения.

Для воспроизводимой проверки без пользовательских данных:

```bash
make mcp-demo
```

Это настоящий MCP-клиент: он запускает сервер через stdio, делает initialize, tools/list и три tools/call. Используется временная база, результат проверяется программно. Подтверждение: [output/mcp-demo.json](output/mcp-demo.json).

## Skills

В OpenCode попросите загрузить skills `playwright` и `context7-mcp`. Подтверждение их обнаружения: [output/opencode-skills.json](output/opencode-skills.json). В локальном запуске модель действительно загрузила оба skill: [output/opencode-demo.json](output/opencode-demo.json).

Для браузерного skill:

```bash
bash .agents/skills/playwright/scripts/playwright_cli.sh --session=practice4 open http://127.0.0.1:8040 --headed
bash .agents/skills/playwright/scripts/playwright_cli.sh --session=practice4 snapshot
```

Далее выполняйте `fill`, `click`, `check` по актуальным ссылкам snapshot; после изменения интерфейса получите новый snapshot. Для проектной установки используйте этот wrapper, а не глобальный путь из примера в исходном skill.

Уже проверено: добавление задачи, поиск, отметка выполнения, фильтр готовых, сохранение статуса после перезагрузки и удаление созданной тестовой задачи. Подтверждения: [создание](output/playwright/01-created.yml), [фильтр](output/playwright/02-completed-filter.yml), [перезагрузка](output/playwright/03-reloaded.yml), [скриншот](output/playwright/completed-task.png). Тестовая задача удалена, пользовательские задачи не удалялись. После первого открытия был обнаружен 404 для favicon; добавлен встроенный пустой favicon, после перезагрузки новая страница открылась без сообщения об ошибке в выводе CLI.

Для Context7:

```bash
.venv/bin/python scripts/demo_context7.py
```

Это реальные вызовы удалённого MCP: `resolve-library-id`, затем `query-docs`. Подтверждение: [output/context7-demo.json](output/context7-demo.json). Ответы основной ветки SDK уже содержат новый API; проверяйте версию перед переносом примера в код. [Разбор skills](SKILLS_REVIEW.md).

## Hook

OpenCode вызывает `tool.execute.after` после `write`, `edit`, `apply_patch`. Обработчик запускает `python3 scripts/check.py` из папки проекта, добавляет `[AUTO CHECK PASS]` или `[AUTO CHECK FAIL]` в ответ инструмента и сохраняет журнал `output/hooks.jsonl`. Таймаут — 45 секунд. Browser E2E не запускается на каждую правку; hook выполняет быстрые локальные проверки.

Hook не отслеживает правки через bash или сторонний редактор. Для них запускайте `make check` вручную. Он сообщает о проблеме после правки; автоматического отката нет.

Проверка исправного и сломанного проекта во временной копии:

```bash
make hook-demo
```

Подтверждение: [output/hook-handler-demo.json](output/hook-handler-demo.json). Здесь вызывается настоящий обработчик plugin, но это не запуск модели внутри OpenCode.

Для короткой демонстрации внутри OpenCode:

```bash
python3 scripts/demo_agent.py --hook-only
```

Модели разрешено читать только README и AGENTS, изменять только README; shell и оба MCP на время этого короткого сценария отключены. Результат runner возвращает hook, а не отдельная команда модели. Перед повторным запуском адаптируйте запрос в `scripts/demo_agent.py` к текущему тексту README либо попросите другую небольшую правку этого файла.

## Ограничения демонстрационных запусков

Облачный `opencode/big-pickle` вернул HTTP 403: [output/opencode-cloud-demo.json](output/opencode-cloud-demo.json).

Локальная Qwen за 180 секунд прочитала правила, загрузила оба skill и вызвала собственный MCP на корректном и ошибочном входе, затем повторно загрузила Context7 skill и не завершила оставшийся сценарий до таймаута. Это частичное подтверждение применения среды; оно не доказывает вызов Context7 или hook этой моделью в том запуске. Запись: [output/opencode-demo.json](output/opencode-demo.json).

Рефлексия по обсуждению, наблюдениям и решениям пользователя находится в [../reflection.md](../reflection.md).

Прежний короткий запуск на Qwen остановился по таймауту: [архив попытки](output/opencode-hook-demo-2026-10-07T19-53-46.725312_00-00.json). Первая попытка на Sonnet выполнила правку и hook, но провайдер отказал на заключительном запросе при лимите шагов: [архив](output/opencode-hook-demo-2026-10-07T20-14-04.810299_00-00.json). После увеличения лимита шагов финальная сессия Sonnet 5.5 завершилась с кодом 0, модель получила `[AUTO CHECK PASS]` и подтвердила семь тестов: [доказательство](output/opencode-hook-demo.json), [журнал hook](output/hooks.jsonl).

## Git

По указанию пользователя ветка `practice_04` создана от `practice_03` в текущем репозитории, без worktree, после подтверждения окончания работы другого агента. База — `df339ce`. PR открывается внутри форка `pikmi064/ITMOv2`, из `practice_04` в `practice_03`, чтобы изменения третьей практики не входили в diff четвёртой. В commit включается только `practices/practice_04`. Удаление корневого `opencode.json` и оставшийся файл практики 3 не входят в изменения практики 4.
