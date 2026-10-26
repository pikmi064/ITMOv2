import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

from deadlines import get_deadlines
from server import validate_task


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "tasks.sqlite3"
        with sqlite3.connect(self.database) as db:
            db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY, title TEXT, subject TEXT, deadline TEXT, done INTEGER)")
            db.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", [
                (1, "Просрочена", "AI", "2026-10-06", 0),
                (2, "Сегодня", "AI", "2026-10-07", 0),
                (3, "Граница", "AI", "2026-10-14", 0),
                (4, "Позже", "AI", "2026-10-15", 0),
                (5, "Выполнена", "AI", "2026-10-06", 1),
                (6, "Без срока", "AI", "", 0),
            ])

    def test_window_excludes_completed_unscheduled_and_later_tasks(self):
        result = get_deadlines(self.database, 7, today=date(2026, 10, 7))
        self.assertEqual([t["id"] for t in result["overdue"]], [1])
        self.assertEqual([t["id"] for t in result["upcoming"]], [2, 3])
        self.assertEqual(result["upcoming"][1]["days_until_deadline"], 7)

    def test_zero_includes_today_and_overdue(self):
        result = get_deadlines(self.database, 0, today=date(2026, 10, 7))
        self.assertEqual(result["counts"], {"overdue": 1, "upcoming": 1})

    def test_invalid_days(self):
        for value in (-1, 366, True, 1.5, "7"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                get_deadlines(self.database, value)

    def test_query_does_not_modify_database(self):
        before = self.database.read_bytes()
        get_deadlines(self.database, 365)
        self.assertEqual(self.database.read_bytes(), before)

    def test_missing_database_is_not_created(self):
        missing = self.database.parent / "missing.sqlite3"
        with self.assertRaisesRegex(ValueError, "не найдена"):
            get_deadlines(missing)
        self.assertFalse(missing.exists())


class InputTests(unittest.TestCase):
    def test_trim_and_validate(self):
        self.assertEqual(validate_task({"title": " Задача ", "subject": " AI ", "deadline": "2026-10-07"}), ("Задача", "AI", "2026-10-07"))

    def test_bad_input(self):
        for value in ([], {"title": " "}, {"title": "x" * 161}, {"title": "x", "deadline": "2026-02-30"}, {"title": "x", "deadline": "20261007"}, {"title": "x", "subject": 42}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_task(value)


if __name__ == "__main__":
    unittest.main()
