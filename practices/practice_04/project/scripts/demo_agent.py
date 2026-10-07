"""Bounded OpenCode run: rules, skills, MCP, one README edit, actual hook."""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = """Work only in this project. Do not use bash and do not touch other practices.
1. Read AGENTS.md using the read tool.
2. Load the playwright and context7-mcp skills using the skill tool. Do not run a browser yourself in this demonstration.
3. Call study_tracker_get_deadlines with days=7, then with days=-1. The second call is an intentional invalid-input demonstration. Report the actual results, including an empty list if returned.
4. Use context7 to query official Python MCP SDK docs about FastMCP stdio tools. Resolve the library first. If the service is unavailable report that instead of inventing a result.
5. Read README.md. Add a short sentence stating that automatic checks run after file edits through OpenCode tools.
Use the edit or apply_patch tool, not bash. Do not modify any other file.
6. Read the AUTO CHECK result appended to the edit tool output. Briefly state whether it passed. Do not manually run the checks: this demonstration must show the automatic hook.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hook-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    (ROOT / "output").mkdir(exist_ok=True)
    config = {"permission": {"bash": "deny", "external_directory": "deny", "edit": {"*": "deny", "**/README.md": "allow"}}}
    prompt = PROMPT
    agent = "build"
    if args.hook_only:
        config["permission"]["read"] = {"*": "deny", "**/README.md": "allow", "**/AGENTS.md": "allow"}
        config["mcp"] = {"context7": {"enabled": False}, "study_tracker": {"enabled": False}}
        config["tools"] = {"skill": False, "bash": False, "glob": False, "grep": False, "webfetch": False, "websearch": False, "todowrite": False, "task": False, "question": False, "lsp": False, "write": False, "apply_patch": False}
        agent = "hook-proof"
        config["agent"] = {agent: {"mode": "primary", "steps": 6, "temperature": 0.1, "prompt": "You edit project documentation using the edit tool. Follow the user's exact replacement. Only README.md may be changed. After editing report the AUTO CHECK marker returned by the tool. Do not run shell commands."}}
        file = ROOT / "README.md"
        variants = [
            "Обработчик проверен отдельно; полную демонстрацию hook внутри модели OpenCode пока остановил таймаут.",
            "Результат автоматической проверки возвращается агенту сразу после изменения файла.",
            "После изменения файла агент получает результат автоматической проверки.",
        ]
        content = file.read_text()
        selected = next((i for i, sentence in enumerate(variants) if sentence in content), None)
        if selected is None:
            raise ValueError("README changed: update the exact replacement in demo_agent.py")
        old, new = variants[selected], variants[1 if selected != 1 else 2]
        prompt = f"Use the edit tool now. filePath: {file}\noldString: {old}\nnewString: {new}\nReplace exactly this sentence; do not change anything else. Then report the AUTO CHECK status returned by the edit tool."
    env = {**os.environ, "OPENCODE_CONFIG_CONTENT": json.dumps(config)}
    model = os.environ.get("P4_DEMO_MODEL", "vsellm/anthropic/claude-sonnet-5.5")
    command = ["opencode", "run", "--agent", agent, "--model", model, "--format", "json", prompt]
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        result = subprocess.CompletedProcess(command, 124, stdout, f"Timed out after {args.timeout} seconds")
    events = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") in ("tool_use", "text", "error", "step_finish"):
            events.append(event)
    evidence = {"time": datetime.now(timezone.utc).isoformat(), "model": model, "agent": agent, "timeout_seconds": args.timeout, "prompt": prompt, "exit_code": result.returncode, "events": events, "stderr": result.stderr[-4000:]}
    destination = "output/opencode-hook-demo.json" if args.hook_only else "output/opencode-demo.json"
    previous = ROOT / destination
    if previous.exists():
        old_result = json.loads(previous.read_text())
        stamp = old_result["time"].replace(":", "-").replace("+", "_")
        previous.rename(previous.with_name(previous.stem + "-" + stamp + previous.suffix))
    (ROOT / destination).write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"exit_code": result.returncode, "event_count": len(events), "tools": [e.get("part", {}).get("tool") for e in events if e.get("type") == "tool_use"], "evidence": destination}, ensure_ascii=False, indent=2))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
