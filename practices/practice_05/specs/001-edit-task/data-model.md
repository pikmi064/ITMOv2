# Data Model
Task(id INTEGER PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT пустая строка, deadline TEXT NOT NULL DEFAULT пустая строка, done INTEGER 0|1 DEFAULT 0).
Миграций нет. Редактирование меняет только title/subject/deadline, сохраняет done/id. State UI: closed → editing → saving → closed или error → editing. Серверная транзакция либо меняет все три поля, либо ни одного.
