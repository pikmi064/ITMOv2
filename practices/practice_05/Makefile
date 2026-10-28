.PHONY: check e2e serve demo spec-check
check:
	cd project && python3 -m unittest discover -s tests -v
	python3 scripts/check_js.py
e2e:
	node project/tests/e2e.cjs
serve:
	python3 project/server.py --port 8050
demo:
	python3 scripts/demo.py
spec-check:
	SPECIFY_FEATURE_DIRECTORY=specs/001-edit-task bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
