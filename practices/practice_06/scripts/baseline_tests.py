"""Run the final regression suite against the pinned vulnerable course service."""
import importlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'lab'))
with tempfile.TemporaryDirectory(prefix='shop-baseline-tests-') as directory:
    for name in ['service.py', 'sandbox.py']:
        data = subprocess.check_output(['git', 'show', f'9156eac:practices/practice_06/lab/{name}'], cwd=root)
        (Path(directory) / name).write_bytes(data)
    sys.path.insert(0, directory)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)) for name in ['test_service', 'test_http', 'test_security'])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
