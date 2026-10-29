"""Local study task tracker. Run: python3 server.py"""

import argparse
import json
import sqlite3
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "data" / "tasks.sqlite3"


def connect():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def validate_task(data):
    if not isinstance(data, dict):
        raise ValueError("Ожидается JSON-объект")
    title = data.get("title")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
        raise ValueError("Название должно содержать от 1 до 160 символов")
    subject = data.get("subject", "")
    if not isinstance(subject, str) or len(subject.strip()) > 80:
        raise ValueError("Название предмета — до 80 символов")
    deadline = data.get("deadline", "")
    if not isinstance(deadline, str):
        raise ValueError("Срок должен быть строкой")
    # Escaped lone surrogates are accepted by json.loads, but cannot be
    # encoded as UTF-8 by SQLite or the JSON response. Reject before SQL.
    try:
        for value in (title, subject, deadline):
            value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Строки должны содержать корректный Unicode") from None
    if deadline:
        try:
            if date.fromisoformat(deadline).isoformat() != deadline:
                raise ValueError()
        except ValueError:
            raise ValueError("Срок должен быть датой в формате YYYY-MM-DD") from None
    return title.strip(), subject.strip(), deadline


def validate_edit(data):
    """PUT replaces exactly the editable fields, never identity or completion."""
    if not isinstance(data, dict) or set(data) != {"title", "subject", "deadline"}:
        raise ValueError("Укажите ровно поля title, subject и deadline")
    return validate_task(data)


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            payload = (ROOT / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif path == "/api/tasks":
            with connect() as db:
                rows = db.execute("SELECT * FROM tasks ORDER BY done, CASE WHEN deadline = '' THEN 1 ELSE 0 END, deadline, id DESC").fetchall()
            self.respond(200, [dict(row) for row in rows])
        else:
            self.respond(404, {"error": "Страница не найдена"})

    def do_POST(self):
        if urlparse(self.path).path != "/api/tasks":
            return self.respond(404, {"error": "Маршрут не найден"})
        try:
            title, subject, deadline = validate_task(self.read_json())
        except (ValueError, UnicodeDecodeError) as error:
            return self.respond(400, {"error": str(error)})
        with connect() as db:
            cursor = db.execute("INSERT INTO tasks(title, subject, deadline) VALUES (?, ?, ?)", (title, subject, deadline))
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        self.respond(201, dict(row))

    def read_json(self):
        lengths = self.headers.get_all("Content-Length", [])
        length = lengths[0] if len(lengths) == 1 else ""
        if not length or not length.isascii() or not length.isdigit():
            raise ValueError("Некорректный Content-Length")
        # Bound before int(): arbitrarily long digit strings must not crash.
        canonical = length.lstrip("0") or "0"
        if len(canonical) > 4 or not 0 < int(canonical) <= 8192:
            raise ValueError("Ожидается JSON размером до 8 КБ")
        size = int(canonical)
        if self.headers.get("Transfer-Encoding") is not None:
            raise ValueError("Transfer-Encoding не поддерживается")
        try:
            return json.loads(self.rfile.read(size).decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Некорректный JSON") from None
        except RecursionError:
            # Older supported Python runtimes enforce parser recursion depth.
            raise ValueError("JSON слишком глубоко вложен") from None

    def do_PATCH(self):
        self.mutate_task(delete=False)

    def do_DELETE(self):
        self.mutate_task(delete=True)

    def task_id(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "tasks"] or not parts[2].isascii() or not parts[2].isdigit():
            return None
        digits = parts[2].lstrip("0") or "0"
        if len(digits) > 19 or not 1 <= int(digits) <= 9223372036854775807:
            return None
        return int(digits)

    def do_PUT(self):
        task_id = self.task_id()
        if task_id is None:
            return self.respond(404, {"error": "Задача или маршрут не найдены"})
        try:
            title, subject, deadline = validate_edit(self.read_json())
        except (ValueError, UnicodeDecodeError) as error:
            return self.respond(400, {"error": str(error)})
        with connect() as db:
            cursor = db.execute(
                "UPDATE tasks SET title = ?, subject = ?, deadline = ? WHERE id = ?",
                (title, subject, deadline, task_id),
            )
            if not cursor.rowcount:
                return self.respond(404, {"error": "Задача не найдена"})
            row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        self.respond(200, dict(row))

    def mutate_task(self, delete):
        task_id = self.task_id()
        if task_id is None:
            return self.respond(404, {"error": "Задача не найдена"})
        if not delete:
            try:
                data = self.read_json()
                if not isinstance(data, dict) or type(data.get("done")) is not bool:
                    raise ValueError("Поле done должно быть true или false")
            except (ValueError, UnicodeDecodeError) as error:
                return self.respond(400, {"error": str(error)})
        with connect() as db:
            if delete:
                cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            else:
                cursor = db.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(data["done"]), task_id))
            if not cursor.rowcount:
                return self.respond(404, {"error": "Задача не найдена"})
        self.respond(200, {"ok": True})


def main():
    global DATABASE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8040)
    parser.add_argument("--database", type=Path, default=DATABASE,
                        help="SQLite path; use a separate temporary path for demos")
    args = parser.parse_args()
    DATABASE = args.database.expanduser().resolve()
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', deadline TEXT NOT NULL DEFAULT '', done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)))")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Учебный трекер: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
