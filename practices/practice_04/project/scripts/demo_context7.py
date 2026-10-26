"""Fetch SDK documentation through the configured remote Context7 MCP."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parents[1]


async def main():
    async with streamablehttp_client("https://mcp.context7.com/mcp", timeout=20, sse_read_timeout=30) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resolved = await session.call_tool("resolve-library-id", {"libraryName": "modelcontextprotocol python-sdk", "query": "Official Python MCP SDK FastMCP stdio server tool validation"})
            # This is the official repository ID. Keep the resolution result for review.
            result = await session.call_tool("query-docs", {"libraryId": "/modelcontextprotocol/python-sdk", "query": "FastMCP @mcp.tool() run transport stdio Python SDK v1"})
            if resolved.isError or result.isError:
                raise RuntimeError("Context7 returned an error: " + str(result.content))
            evidence = {"time": datetime.now(timezone.utc).isoformat(), "url": "https://mcp.context7.com/mcp", "resolve": resolved.model_dump(mode="json", exclude_none=True), "query": result.model_dump(mode="json", exclude_none=True)}
            (ROOT / "output").mkdir(exist_ok=True)
            (ROOT / "output/context7-demo.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
            print("PASS: Context7 resolve-library-id and query-docs; evidence: output/context7-demo.json")


if __name__ == "__main__":
    asyncio.run(main())
