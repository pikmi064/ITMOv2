"""Verify saved evidence and local document links; preserve a JSON report."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    def read(name):
        return json.loads((ROOT / "output" / name).read_text())

    findings = []

    def record(name, passed):
        findings.append({"check": name, "status": "PASS" if passed else "FAIL"})

    mcp = read("mcp-demo.json")
    record("MCP success and both invalid inputs", mcp["assertions"] == "PASS" and not mcp["calls"][0]["result"]["isError"] and all(call["result"]["isError"] for call in mcp["calls"][1:]))
    hooks = read("hook-handler-demo.json")
    record("Hook handler PASS, FAIL, and skipped read", hooks["assertions"] == "PASS" and "[AUTO CHECK PASS]" in hooks["pass"] and "[AUTO CHECK FAIL]" in hooks["fail"] and hooks["readSkipped"])
    context7 = read("context7-demo.json")
    record("Context7 resolve and docs returned content", all(context7[key].get("content") and not context7[key].get("isError", False) for key in ("resolve", "query")))
    agent = read("opencode-demo.json")
    tool_events = [e["part"] for e in agent["events"] if e["type"] == "tool_use"]
    record("Agent read rules", any(e["tool"] == "read" and e["state"]["input"]["filePath"].endswith("AGENTS.md") and e["state"]["status"] == "completed" for e in tool_events))
    record("Agent loaded both skills", {e["state"]["input"].get("name") for e in tool_events if e["tool"] == "skill" and e["state"]["status"] == "completed"} >= {"playwright", "context7-mcp"})
    record("Agent invoked MCP success and invalid input", any(e["tool"] == "study_tracker_get_deadlines" and e["state"]["status"] == "completed" for e in tool_events) and any(e["tool"] == "study_tracker_get_deadlines" and e["state"]["status"] == "error" and e["state"]["input"] == {"days": -1} for e in tool_events))
    proof = read("opencode-hook-demo.json")
    edits = [e["part"] for e in proof["events"] if e["type"] == "tool_use" and e["part"]["tool"] == "edit"]
    record("Successful Sonnet OpenCode session", proof["exit_code"] == 0 and proof["model"] == "vsellm/anthropic/claude-sonnet-5.5")
    record("Real edit received AUTO CHECK PASS", any(e["state"]["status"] == "completed" and "[AUTO CHECK PASS]" in e["state"].get("output", "") for e in edits))
    journal = [json.loads(line) for line in (ROOT / "output/hooks.jsonl").read_text().splitlines()]
    record("Hook log matches actual tool callID", any(e["callID"] == row["callID"] and row["status"] == "PASS" for e in edits for row in journal))
    text = "\n".join(e["part"]["text"] for e in proof["events"] if e["type"] == "text")
    record("Agent acknowledged automatic checks", "AUTO CHECK" in text and "PASS" in text and "7" in text)
    record("Runner reported seven passing tests", "Ran 7 tests" in (ROOT / "output/checks.txt").read_text() and "PASS: all checks" in (ROOT / "output/checks.txt").read_text())
    browser = ROOT / "output/playwright"
    record("Browser snapshots: created, completed, reloaded, cleaned", "Проверка Playwright" in (browser / "01-created.yml").read_text() and "[checked]" in (browser / "02-completed-filter.yml").read_text() and "[checked]" in (browser / "03-reloaded.yml").read_text() and "Начнём с одной задачи" in (browser / "04-cleaned.txt").read_text())
    documents = [ROOT.parent / "README.md", ROOT / "README.md", ROOT / "EVIDENCE.md", ROOT / "DEMO.md", ROOT / "SKILLS_REVIEW.md", ROOT.parent / "reflection.md", ROOT / "REVIEW.md"]
    links = []
    for document in documents:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if target.startswith(("http:", "https:", "#")):
                continue
            links.append({"source": str(document.relative_to(ROOT.parent)), "target": target, "exists": (document.parent / target.split("#")[0]).is_file()})
    record("All local document link targets exist", all(link["exists"] for link in links))
    report = {"time": datetime.now(timezone.utc).isoformat(), "status": "PASS" if all(f["status"] == "PASS" for f in findings) else "FAIL", "checks": findings, "local_links": links, "scope": "saved evidence and file links; not a new browser/model run"}
    (ROOT / "output/evidence-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "output/document-links.json").write_text(json.dumps({
        "time": report["time"], "check": "relative Markdown link target files; external URLs and anchors excluded",
        "files": [str(file.relative_to(ROOT.parent)) for file in documents],
        "checked_local_links": len(links), "missing": [link for link in links if not link["exists"]],
        "status": "PASS" if all(link["exists"] for link in links) else "FAIL", "entries": links,
    }, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(findings), "failed": [f["check"] for f in findings if f["status"] == "FAIL"]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
