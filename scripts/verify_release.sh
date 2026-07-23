#!/usr/bin/env bash
set -euo pipefail
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=continuityos --cov-report=term-missing --cov-fail-under=85
uv build
PYTHONPATH=src uv run python scripts/demo.py > /tmp/continuityos-demo.json
python -m json.tool /tmp/continuityos-demo.json >/dev/null
PYTHONPATH=src uv run python scripts/evidence_smoke.py > /tmp/continuityos-evidence.json
python -m json.tool /tmp/continuityos-evidence.json >/dev/null
printf 'release verification passed\n'
