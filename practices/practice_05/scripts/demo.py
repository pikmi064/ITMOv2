"""Run a disposable demonstration, never the student's personal database."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='practice5-demo-') as directory:
    print('Демо: http://127.0.0.1:8050 — отдельная временная база. Ctrl+C завершает.', flush=True)
    try:
        subprocess.run([sys.executable, str(root / 'project/server.py'), '--port', '8050', '--database', str(Path(directory) / 'demo.sqlite3')], check=True)
    except KeyboardInterrupt:
        pass
