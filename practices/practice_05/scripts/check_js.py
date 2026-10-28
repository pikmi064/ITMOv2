"""Check the actual inline JavaScript without touching application data."""
import re
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    for number, content in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>', (root / 'project/index.html').read_text(), re.S | re.I)):
        script = Path(directory) / f'{number}.js'
        script.write_text(content)
        subprocess.run(['node', '--check', str(script)], check=True)
print('PASS: inline JavaScript syntax')
