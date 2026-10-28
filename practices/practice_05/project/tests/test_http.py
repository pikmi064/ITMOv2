"""Contract tests over real HTTP with isolated SQLite, never user data."""

import http.client
import json
import os
import select
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import server


SCHEMA = "CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', deadline TEXT NOT NULL DEFAULT '', done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)))"
VALID = {"title": " Исправлено ", "subject": " AI ", "deadline": "2028-02-29"}


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "tasks.sqlite3"
        self.original_database = server.DATABASE
        server.DATABASE = self.database
        self.addCleanup(setattr, server, "DATABASE", self.original_database)
        with sqlite3.connect(self.database) as db:
            db.execute(SCHEMA)
            db.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", [
                (1, "Первая", "Old", "2026-01-01", 0),
                (2, "Вторая", "Old", "2026-01-02", 1),
            ])
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()

    def request(self, method, path="/api/tasks/1", data=None, *, raw=None, headers=None):
        connection = http.client.HTTPConnection(*self.httpd.server_address, timeout=3)
        body = raw if raw is not None else json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        try:
            connection.request(method, path, body=body, headers=headers or {"Content-Type": "application/json"})
            response = connection.getresponse()
            payload = response.read()
            content_type = response.getheader("Content-Type")
            if path == "/":
                return response.status, payload
            self.assertIn("application/json", content_type or "")
            return response.status, json.loads(payload)
        finally:
            connection.close()

    def rows(self):
        with sqlite3.connect(self.database) as db:
            return db.execute("SELECT * FROM tasks ORDER BY id").fetchall()

    def assert_rejected(self, data=None, *, status=400, path="/api/tasks/1", raw=None, headers=None):
        before = self.rows()
        actual, body = self.request("PUT", path, data, raw=raw, headers=headers)
        self.assertEqual(actual, status, body)
        self.assertIsInstance(body.get("error"), str)
        self.assertTrue(body["error"])
        self.assertEqual(self.rows(), before)

    def test_edit_keeps_id_done_and_other_task(self):
        for task_id, done in ((1, 0), (2, 1)):
            other = [r for r in self.rows() if r[0] != task_id]
            status, body = self.request("PUT", f"/api/tasks/{task_id}", VALID)
            self.assertEqual(status, 200)
            self.assertEqual(body, {"id": task_id, "title": "Исправлено", "subject": "AI", "deadline": "2028-02-29", "done": done})
            self.assertEqual([r for r in self.rows() if r[0] != task_id], other)
            self.assertIn(body, self.request("GET", "/api/tasks")[1])

    def test_clear_optional_and_idempotent(self):
        value = {"title": "x", "subject": "", "deadline": ""}
        first = self.request("PUT", data=value)
        self.assertEqual(first[0], 200)
        before = self.rows()
        self.assertEqual(self.request("PUT", data=value), first)
        self.assertEqual(self.rows(), before)
        self.assertEqual(first[1]["subject"], "")
        self.assertEqual(first[1]["deadline"], "")

    def test_lengths_and_python_unicode_characters(self):
        value = {"title": "😀" * 160, "subject": "Я" * 80, "deadline": ""}
        status, body = self.request("PUT", data=value)
        self.assertEqual(status, 200)
        self.assertEqual(body["title"], value["title"])
        self.assertEqual(body["subject"], value["subject"])
        for key, over in (("title", "x" * 161), ("subject", "x" * 81)):
            self.assert_rejected({**VALID, key: over})

    def test_limits_after_trim(self):
        status, body = self.request("PUT", data={"title": " " + "x" * 160 + " ", "subject": " " + "y" * 80 + " ", "deadline": ""})
        self.assertEqual(status, 200)
        self.assertEqual((len(body["title"]), len(body["subject"])), (160, 80))

    def test_dates(self):
        for value in ("2028-02-29", "0001-01-01", "9999-12-31", "2000-01-01", ""):
            with self.subTest(value=value):
                self.assertEqual(self.request("PUT", data={**VALID, "deadline": value})[0], 200)
        for value in ("2026-02-29", "2026-02-30", "20261028", "2026-1-01", "2026-10-28 ", " 2026-10-28", "2026-W01-1", "0000-01-01"):
            with self.subTest(value=value):
                self.assert_rejected({**VALID, "deadline": value})

    def test_wrong_types_and_blank_title(self):
        for data in ([], None, "text", 1, True, {}, {**VALID, "title": " \t\n "}):
            with self.subTest(data=data):
                self.assert_rejected(raw=json.dumps(data).encode())
        for key in VALID:
            for value in (None, True, 42, [], {}):
                with self.subTest(key=key, value=value):
                    self.assert_rejected({**VALID, key: value})

    def test_exact_keys(self):
        for key in VALID:
            self.assert_rejected({k: v for k, v in VALID.items() if k != key})
        for key, value in (("id", 1), ("done", True), ("titel", "x")):
            self.assert_rejected({**VALID, key: value})

    def test_json_utf8_and_size(self):
        for raw in (b"", b"{", b"{\"title\":\"\xff\"}", b" " * 8193):
            with self.subTest(raw=raw[:30]):
                self.assert_rejected(raw=raw)
        # Exactly 8192 bytes is parsed and can contain whitespace padding.
        raw = json.dumps({"title": "ok", "subject": "", "deadline": ""}).encode()
        self.assertEqual(self.request("PUT", raw=raw + b" " * (8192 - len(raw)))[0], 200)

    def test_escaped_unpaired_unicode_surrogates(self):
        for key in ("title", "subject"):
            for value in ("\ud800", "\udfff"):
                with self.subTest(key=key, codepoint=hex(ord(value))):
                    # ASCII JSON bytes are valid UTF-8, but the decoded value
                    # cannot be encoded by SQLite. Reject before any write.
                    raw = json.dumps({**VALID, key: value}, ensure_ascii=True).encode("ascii")
                    self.assert_rejected(raw=raw)

    def test_json_nesting_limit_is_controlled_error(self):
        raw = b'{"title":' + b"[" * 1500 + b"0" + b"]" * 1500 + b',"subject":"","deadline":""}'
        self.assertLess(len(raw), 8192)
        self.assert_rejected(raw=raw)

    def test_malformed_content_length(self):
        for length in ("wat", "-1", "0", "8193", "+50", "1.0"):
            with self.subTest(length=length):
                self.assert_rejected(raw=b"{}", headers={"Content-Length": length})

    def test_missing_content_length(self):
        # Explicit low-level request avoids http.client adding Content-Length.
        before = self.rows()
        connection = http.client.HTTPConnection(*self.httpd.server_address, timeout=3)
        try:
            connection.putrequest("PUT", "/api/tasks/1")
            connection.endheaders()
            response = connection.getresponse()
            body = json.loads(response.read())
            self.assertEqual(response.status, 400)
            self.assertIn("error", body)
            self.assertEqual(self.rows(), before)
        finally:
            connection.close()

    def test_not_found_and_id_boundaries(self):
        for path in ("/api/tasks/0", "/api/tasks/-1", "/api/tasks/1.0", "/api/tasks/%D9%A1", "/api/tasks/9223372036854775808", "/api/tasks/" + "9" * 5000, "/api/task/1", "/api/tasks/1/extra"):
            with self.subTest(path=path[:70]):
                self.assert_rejected(VALID, status=404, path=path)
        for value in ("999", "9223372036854775807"):
            self.assert_rejected(VALID, status=404, path="/api/tasks/" + value)
        self.assertEqual(self.request("PUT", "/api/tasks/0001", VALID)[0], 200)

    def test_validation_order(self):
        self.assert_rejected({}, status=404, path="/api/tasks/0")
        self.assert_rejected({}, status=400, path="/api/tasks/999")

    def test_sql_and_html_are_data(self):
        title = "<script>alert(1)</script>'); DROP TABLE tasks;--"
        status, body = self.request("PUT", data={**VALID, "title": title})
        self.assertEqual(status, 200)
        self.assertEqual(body["title"], title)
        self.assertEqual(len(self.rows()), 2)

    def test_old_crud_and_sort(self):
        self.assertEqual(self.request("GET", "/")[0], 200)
        status, created = self.request("POST", "/api/tasks", {"title": "Новая", "deadline": "2025-01-01"})
        self.assertEqual(status, 201)
        task_id = created["id"]
        self.assertEqual(self.request("GET", "/api/tasks")[1][0]["id"], task_id)
        self.assertEqual(self.request("PATCH", f"/api/tasks/{task_id}", {"done": True}), (200, {"ok": True}))
        self.assertEqual(self.request("GET", "/api/tasks")[1][0]["id"], 1)
        self.assertEqual(self.request("PATCH", f"/api/tasks/{task_id}", {"done": False}), (200, {"ok": True}))
        self.assertEqual(self.request("DELETE", f"/api/tasks/{task_id}"), (200, {"ok": True}))
        self.assertEqual(len(self.rows()), 2)
        self.assertEqual(self.request("POST", "/api/tasks", {"title": " "})[0], 400)
        self.assertEqual(self.request("PATCH", "/api/tasks/1", {"done": "yes"})[0], 400)
        self.assertEqual(self.request("DELETE", "/api/tasks/999")[0], 404)

    def test_updated_deadline_changes_server_order(self):
        self.request("PATCH", "/api/tasks/2", {"done": False})
        self.assertEqual(self.request("GET", "/api/tasks")[1][0]["id"], 1)
        self.assertEqual(self.request("PUT", "/api/tasks/1", {**VALID, "deadline": ""})[0], 200)
        self.assertEqual(self.request("GET", "/api/tasks")[1][0]["id"], 2)


class RestartTests(unittest.TestCase):
    def test_cli_database_and_persistence_after_process_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / "nested" / "demo.sqlite3"
            process = None

            def start():
                nonlocal process
                process = subprocess.Popen([sys.executable, str(Path(server.__file__).resolve()), "--port", "0", "--database", str(database)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                ready, _, _ = select.select([process.stdout], [], [], 5)
                self.assertTrue(ready, "server did not announce its URL")
                line = process.stdout.readline().strip()
                self.assertIn("http://127.0.0.1:", line)
                return int(line.rsplit(":", 1)[1])

            def call(port, method, path, data=None):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                try:
                    connection.request(method, path, json.dumps(data).encode() if data is not None else None)
                    response = connection.getresponse()
                    result = json.loads(response.read())
                    self.assertLess(response.status, 300, result)
                    return result
                finally:
                    connection.close()

            def stop():
                if process is not None:
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=5)
                    process.stdout.close()

            try:
                port = start()
                task = call(port, "POST", "/api/tasks", {"title": "До"})
                call(port, "PATCH", f"/api/tasks/{task['id']}", {"done": True})
                saved = call(port, "PUT", f"/api/tasks/{task['id']}", VALID)
                stop()
                port = start()
                self.assertEqual(call(port, "GET", "/api/tasks"), [saved])
                self.assertEqual(saved["done"], 1)
            finally:
                stop()


if __name__ == "__main__":
    unittest.main()
