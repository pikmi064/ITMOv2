"""Real MCP calls over stdio, with a temporary fixture database."""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def main():
    today = date.today()
    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "demo.sqlite3"
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE tasks(id INTEGER PRIMARY KEY, title TEXT, subject TEXT, deadline TEXT, done INTEGER)")
            db.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", [
                (1, "Сдать практику 4", "AI-инструменты", (today + timedelta(days=2)).isoformat(), 0),
                (2, "Разобрать конспект", "Математика", (today - timedelta(days=1)).isoformat(), 0),
                (3, "Уже сдано", "AI-инструменты", today.isoformat(), 1),
            ])
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "mcp_server.py")], env={**os.environ, "STUDY_TRACKER_DB": str(database)})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                calls = []
                for arguments in ({"days": 7}, {"days": -1}, {"days": "7"}):
                    result = await session.call_tool("get_deadlines", arguments)
                    calls.append({"arguments": arguments, "result": result.model_dump(mode="json", exclude_none=True)})
                assert not calls[0]["result"].get("isError")
                assert calls[1]["result"]["isError"] and calls[2]["result"]["isError"]
                payload = calls[0]["result"].get("structuredContent")
                if payload is None:
                    payload = json.loads(calls[0]["result"]["content"][0]["text"])
                assert payload["counts"] == {"overdue": 1, "upcoming": 1}
                assert payload["overdue"][0]["id"] == 2
                assert payload["upcoming"][0]["id"] == 1
                evidence = {"time": datetime.now(timezone.utc).isoformat(), "transport": "stdio", "data": "temporary fixture, not user tasks", "server": initialized.model_dump(mode="json"), "tools": tools.model_dump(mode="json"), "calls": calls, "assertions": "PASS"}
                (ROOT / "output").mkdir(exist_ok=True)
                (ROOT / "output/mcp-demo.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
                print(json.dumps({"assertions": "PASS", "counts": payload["counts"], "invalid_negative": calls[1]["result"]["isError"], "invalid_string": calls[2]["result"]["isError"], "evidence": "output/mcp-demo.json"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
