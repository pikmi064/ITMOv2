"""Study tracker MCP. stdout is reserved for the stdio protocol."""

import os
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from deadlines import get_deadlines as query_deadlines

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("STUDY_TRACKER_DB", ROOT / "data/tasks.sqlite3"))
mcp = FastMCP("after-class")


@mcp.tool()
def get_deadlines(days: Annotated[int, Field(strict=True, ge=0, le=365)] = 7) -> dict:
    """Read unfinished overdue tasks and upcoming deadlines from the study tracker.

    days is an integer from 0 to 365. The upcoming interval includes today
    through today + days, inclusive; 0 means today only. Overdue tasks are
    always included. Completed tasks and tasks without a deadline are excluded.
    Uses the computer's local date and opens SQLite read-only.
    """
    return query_deadlines(DATABASE, days)


if __name__ == "__main__":
    mcp.run(transport="stdio")
