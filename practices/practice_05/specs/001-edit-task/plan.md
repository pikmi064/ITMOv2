# Implementation Plan: Редактирование задачи

**Branch**: codex/practice-05 | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

## Summary
Продолжить трекер практики 4 в изолированном snapshot project/. Добавить отдельный PUT редактируемых полей и native dialog. Спецификации двух команд и contracts/api.md согласуются до кода.

## Technical Context
Python 3.11+ stdlib HTTPServer/SQLite; HTML/CSS/vanilla JS; без runtime зависимостей. Tests: unittest через настоящий HTTP, Playwright Chromium для браузера. Локальный однопользовательский сервис, bind 127.0.0.1, до нескольких сотен задач; оптимизация производительности не входит в изменение. Проверки offline, только установка dev tools использует сеть.

## Constitution Check
I: исходные и итоговые спеки, контракт и коммит до кода. II: прежние 7 unit + HTTP regression. III: E2E и отдельный ревьюер. IV: --database указывает временную БД. V: решения принял агент по поручению пользователя. Нарушений нет.

## Project Structure
- project/server.py, index.html, deadlines.py — snapshot из практики 4, без базы.
- project/tests/test_project.py — исходные unit.
- project/tests/test_http.py — новый контракт и регрессия.
- project/tests/e2e.cjs — сквозные UI/API, отдельная временная база.
- Makefile — check, e2e, serve, demo.
- evidence/ — baseline, CLI, тесты, скриншоты, согласование и review.

## Phase 0: Research
См. research.md: текущее поведение и выбор PUT вместо расширения PATCH.
## Phase 1: Design
См. data-model.md, contracts/api.md, ui.md, logic.md. Один UPDATE трёх полей; dialog блокирует повтор и отмену во время запроса. После 200 локальный ответ сохраняется до GET.
## Phase 2: Tasks
См. tasks.md. Сначала HTTP-тесты с red запуском, затем backend, затем UI и E2E, документация и независимое ревью.

## Complexity Tracking
Нарушений нет. Snapshot позволяет сдавать ДЗ5 без изменения проверенной практики 4; происхождение фиксируется хешем исходного commit.
