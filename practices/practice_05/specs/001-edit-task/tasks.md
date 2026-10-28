# Tasks: Редактирование задачи

Input: spec.md, ui.md, logic.md, plan.md, contracts/api.md.

## Phase 1: Setup
- [X] T001 Зафиксировать согласование двух команд и отдельный pre-code commit; project пока отсутствует.
- [X] T002 Скопировать baseline server/index/deadlines и tests/test_project.py из практики 4 без данных; добавить --database для безопасных запусков.

## Phase 2: US1 — сохранить исправление
- [X] T003 [US1] Написать project/tests/test_http.py для PUT и старых API, получить red на отсутствии PUT.
- [X] T004 [US1] Реализовать атомарный PUT в project/server.py, прогнать HTTP-тесты.
- [X] T005 [US1] Добавить native dialog и изменение полей в project/index.html.

## Phase 3: US2 — отмена и ошибки
- [X] T006 [US2] Проверить 400/404/некорректные тела/id, no partial write в project/tests/test_http.py.
- [X] T007 [US2] Реализовать draft/error/blocking/focus и различение PUT success/GET fail в project/index.html.

## Phase 4: US3 — совместимость
- [X] T008 [US3] Написать project/tests/e2e.cjs: save/reload/restart, отмена, ошибки/сеть, поиск/фильтр, done/delete, keyboard, narrow viewport.
- [X] T009 Добавить Makefile/CI, фактические evidence и короткое демо с отдельной базой.
- [X] T010 Написать README, сравнение OpenSpec, reflection и ПОЯСНЕНИЕ.md.
- [ ] T011 Независимый субагент: повторить тесты и проверить rubric 2+2+5+1, устранить существенные замечания.
- [ ] T012 Converge по spec/plan/tasks; commit, push, PR с базой main внутри форка.

Dependencies: T001 → T002 → T003 → T004 → T005/T007 → T008 → T009/T010 → T011 → T012. До T001 код не создаётся. T012 помечается после реального создания PR.
