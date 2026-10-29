# Исправление удержания клавиатурного фокуса

Дата: 2026-10-28, Europe/Moscow. Выполнил отдельный агент команды UI после сообщения основного агента о падении E2E. Проверялся настоящий Chrome через Playwright, а не модель DOM. Основной E2E не изменялся.

## Воспроизведение

Независимый probe запускал `project/server.py --port 0 --database <отдельная временная папка>/tasks.sqlite3`, создавал одну задачу через HTTP, открывал настоящий UI в Chrome, нажимал кнопку изменения, затем 12 раз Tab и 12 раз Shift+Tab. После каждого перехода записывал `document.activeElement` и результат `document.querySelector('#editor').contains(document.activeElement)`. Сервер, браузер и временная база удалены после проверки; пользовательская база не использовалась.

Команда запуска: `NODE_PATH=/Users/danil/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules PLAYWRIGHT_CHANNEL=chrome node /tmp/practice5-focus-probe.cjs`. Версия Chrome: 155.0.8059.85.

Ожидание: каждый переход внутри открытого модального редактора. Факт до исправления: восьмой Tab после начального фокуса в title переводил activeElement в BODY; следующий Tab возвращал title. Обратный полный обход также достигал BODY. Следовательно, одно showModal в этом браузере не удовлетворяло точному условию AC5.

## Исправление

В `project/index.html` добавлен явный переход с последней кнопки «Сохранить» к первому полю и обратный переход Shift+Tab. Внутренние сегменты date input используют прежнее нативное поведение. Во время PUT фокус перемещается на сам dialog с tabindex=-1; Tab/Shift+Tab блокируются до ответа. Отмена и Escape во время сохранения по-прежнему запрещены. При ошибке ввода возвращается фокус в title с сохранённым черновиком.

## Фактические результаты

| Проверка | До | После |
|---|---|---|
| Tab 7 | BUTTON #edit-save, внутри=True | BUTTON #edit-save, внутри=True |
| Tab 8 | BODY #(пусто), внутри=False | INPUT #edit-title, внутри=True |
| Tab 9 | INPUT #edit-title, внутри=True | INPUT #edit-subject, внутри=True |
| Shift+Tab 12 | BODY #(пусто), внутри=False | INPUT #edit-title, внутри=True |

После исправления все 24 перехода (12 Tab + 12 Shift+Tab) оставались внутри dialog: PASS. Дополнительный probe задерживал настоящий PUT, проверял Tab, Shift+Tab и Escape, затем разрешал запрос; dialog оставался открыт и фокус был DIALOG #editor на каждом шаге: PASS. После разрешения PUT редактор закрылся. `node --check` inline JS: PASS.

Полные записи отдельного probe (до / после / сохранение):

```json
{
  "before": {
    "browser": "155.0.8059.85",
    "rows": [
      {
        "key": "initial",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 1",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 2",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 3",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 4",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 5",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 6",
        "id": "edit-cancel",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Tab 7",
        "id": "edit-save",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Tab 8",
        "id": "",
        "tag": "BODY",
        "inside": false
      },
      {
        "key": "Tab 9",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 10",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 11",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 12",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 1",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 2",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 3",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 4",
        "id": "edit-save",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Shift+Tab 5",
        "id": "edit-cancel",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Shift+Tab 6",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 7",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 8",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 9",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 10",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 11",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 12",
        "id": "",
        "tag": "BODY",
        "inside": false
      }
    ]
  },
  "after": {
    "browser": "155.0.8059.85",
    "rows": [
      {
        "key": "initial",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 1",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 2",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 3",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 4",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 5",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 6",
        "id": "edit-cancel",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Tab 7",
        "id": "edit-save",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Tab 8",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 9",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 10",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 11",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Tab 12",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 1",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 2",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 3",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 4",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 5",
        "id": "edit-save",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Shift+Tab 6",
        "id": "edit-cancel",
        "tag": "BUTTON",
        "inside": true
      },
      {
        "key": "Shift+Tab 7",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 8",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 9",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 10",
        "id": "edit-deadline",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 11",
        "id": "edit-subject",
        "tag": "INPUT",
        "inside": true
      },
      {
        "key": "Shift+Tab 12",
        "id": "edit-title",
        "tag": "INPUT",
        "inside": true
      }
    ]
  },
  "saving": [
    {
      "key": "saving initial",
      "id": "editor",
      "tag": "DIALOG",
      "inside": true
    },
    {
      "key": "saving Tab",
      "id": "editor",
      "tag": "DIALOG",
      "inside": true
    },
    {
      "key": "saving Shift+Tab",
      "id": "editor",
      "tag": "DIALOG",
      "inside": true
    },
    {
      "key": "saving Escape",
      "id": "editor",
      "tag": "DIALOG",
      "inside": true
    }
  ]
}
```
