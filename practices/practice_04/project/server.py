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
    if deadline:
        try:
            if date.fromisoformat(deadline).isoformat() != deadline:
                raise ValueError()
        except ValueError:
            raise ValueError("Срок должен быть датой в формате YYYY-MM-DD") from None
    return title.strip(), subject.strip(), deadline


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
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 8192:
            raise ValueError("Ожидается JSON размером до 8 КБ")
        try:
            return json.loads(self.rfile.read(size))
        except json.JSONDecodeError:
            raise ValueError("Некорректный JSON") from None

    def do_PATCH(self):
        self.mutate_task(delete=False)

    def do_DELETE(self):
        self.mutate_task(delete=True)

    def mutate_task(self, delete):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["api", "tasks"] or not parts[2].isascii() or not parts[2].isdigit():
            return self.respond(404, {"error": "Маршрут не найден"})
        task_id = int(parts[2])
        if task_id > 9223372036854775807:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8040)
    args = parser.parse_args()
    DATABASE.parent.mkdir(exist_ok=True)
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', deadline TEXT NOT NULL DEFAULT '', done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)))")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Учебный трекер: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
