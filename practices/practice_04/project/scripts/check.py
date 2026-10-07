"""Fast offline checks. Never writes to the user's task database."""

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    try:
        for folder in (ROOT, ROOT / "scripts", ROOT / "tests"):
            for file in folder.glob("*.py"):
                ast.parse(file.read_text(), filename=str(file))
        print("PASS: Python syntax", flush=True)
        html = (ROOT / "index.html").read_text()
        scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)
        if not scripts:
            raise ValueError("Inline JavaScript not found")
        with tempfile.TemporaryDirectory() as folder:
            for number, script in enumerate(scripts):
                file = Path(folder) / f"inline-{number}.js"
                file.write_text(script)
                subprocess.run(["node", "--check", str(file)], check=True, timeout=10)
        subprocess.run(["node", "--check", str(ROOT / ".opencode/plugins/check.js")], check=True, timeout=10)
        print("PASS: JavaScript syntax", flush=True)
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True, timeout=20)
        print("PASS: all checks", flush=True)
        return 0
    except (SyntaxError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
