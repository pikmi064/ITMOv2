# Проверяемые подтверждения ДЗ5

| Шаг / команда | Ожидание | Факт и исходный артефакт |
|---|---|---|
| Прочитать презентацию | Все страницы, включая rubric | 16 страниц, SHA256 bb2e50644e870b7834cfeddfaf9be5365ae6d625572a1a27a9d0f4f90e05a25b; pdftotext + визуальная проверка render всех страниц |
| `python3 -m unittest discover -s tests -v` в baseline | Исходное поведение исправно | 7/7, [baseline.txt](evidence/baseline.txt) |
| `specify version` | Реальный другой framework | v1.2.4, [version](evidence/spec-kit-version.txt) |
| `specify init --here --force --non-interactive --integration codex --integration-options=--skills --script sh --ignore-agent-tools` | Созданы tools/templates | Успех, [init](evidence/spec-kit-init.txt) |
| Template resolver + setup-plan + setup-tasks | Настоящее применение scaffolding | [constitution](evidence/constitution-template.json), [spec](evidence/spec-template.json), [plan](evidence/setup-plan.json), [tasks](evidence/setup-tasks.json) |
| `make spec-check` | Feature docs обнаружены | [prerequisites](evidence/spec-kit-prerequisites.json); это структура, не проверка логики |
| Согласование двух агентов | Общие поля, API, ошибки и состояния | [UI](evidence/ui-agreement.md), [logic](evidence/logic-agreement.md), source drafts сохранены; pre-code commit ca88739 |
| HTTP suite до PUT | Тесты должны обнаружить отсутствие фичи | Ожидаемый RED, [http-red.txt](evidence/http-red.txt) |
| `make check` | HTTP/unit green, JS валиден | [http-tests.txt](evidence/http-tests.txt) (первый GREEN 23), [robustness 25 + RED surrogate](evidence/http-robustness.txt), [final-check.txt](evidence/final-check.txt) |
| Первый browser run | Проверить клавиатуру | Найден выход focus в BODY, [initial-browser-failure.txt](evidence/initial-browser-failure.txt), [разбор/исправление](evidence/focus-fix.md) |
| `PLAYWRIGHT_CHANNEL=chrome make e2e` | AC1–AC5 и регрессия | 12 сценариев PASS, [browser-tests.txt](evidence/browser-tests.txt), [JSON ожидание/факт](evidence/browser-results.json) |
| Независимый субагент | Повторить проверки и сверить rubric | [REVIEW.md](REVIEW.md) с собственными командами/выводами |

Браузерные сбои PUT/GET специально инъецированы маршрутизацией Playwright и явно названы в JSON. Сохранение и остальные операции идут через настоящий HTTP и SQLite. 404 получается настоящим удалением записи другим клиентом. Ни одна инъекция не выдаётся за случайный реальный отказ production-сервиса.

Скриншоты: [desktop dialog](evidence/demo-editor.png), [375px list](evidence/demo-mobile.png), [375px dialog](evidence/demo-mobile-editor.png). Они дополняют проверки поведения. Для интерактивного воспроизведения шагов: `npx playwright show-trace evidence/browser-trace.zip` (trace содержит только синтетические данные тестов).

Неуспешные предварительные команды: sandbox не имел сетевого доступа; установка CLI повторена с разрешённым network вызовом. Первый setup-tasks до spec.md отказал, после создания спецификации повторён успешно. Первый npm lockfile install завис и был остановлен; повтор с ограничением времени завершён. Эти попытки не заявляются успешными проверками.

Независимый финальный контроль: [26 tests](evidence/reviewer-check-after.txt), [12 E2E](evidence/reviewer-e2e-after.txt), [подлинный framework](evidence/reviewer-provenance.json). Замечание: [UTF-16/32 до](evidence/reviewer-encoding-before.txt) → [400 без записи после](evidence/reviewer-encoding-after.txt). У текстовых CLI-логов удалены только концевые пробелы строк для Git hygiene.
