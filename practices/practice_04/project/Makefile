.PHONY: serve setup check mcp-demo hook-demo
serve:
	python3 server.py
setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements-mcp.txt
check:
	python3 scripts/check.py
mcp-demo:
	.venv/bin/python scripts/demo_mcp.py
hook-demo:
	node scripts/demo_hook.mjs
