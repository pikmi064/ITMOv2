"""Read-only deadline queries shared by MCP and checks."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path


def get_deadlines(database: Path, days: int = 7, *, today: date | None = None) -> dict:
    if type(days) is not int or not 0 <= days <= 365:
        raise ValueError("days должен быть целым числом от 0 до 365")
    today = today or date.today()
    through = today + timedelta(days=days)
    if not database.is_file():
        raise ValueError("База задач не найдена. Сначала запустите python3 server.py")
    try:
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT id, title, subject, deadline FROM tasks "
                "WHERE done = 0 AND deadline <> '' AND deadline <= ? "
                "ORDER BY deadline, id", (through.isoformat(),)
            ).fetchall()
    except sqlite3.Error as error:
        raise ValueError("Не удалось прочитать базу задач: проверьте её схему и доступность") from error
    overdue, upcoming = [], []
    for row in rows:
        task = dict(row)
        task["days_until_deadline"] = (date.fromisoformat(task["deadline"]) - today).days
        (overdue if task["deadline"] < today.isoformat() else upcoming).append(task)
    return {"today": today.isoformat(), "through": through.isoformat(),
            "overdue": overdue, "upcoming": upcoming,
            "counts": {"overdue": len(overdue), "upcoming": len(upcoming)}}
