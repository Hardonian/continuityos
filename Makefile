.PHONY: install lint typecheck test coverage build demo evidence iac doctor verify clean keys

install:
	uv sync --all-extras

setup: install

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest

coverage:
	uv run pytest --cov=continuityos --cov-report=term-missing --cov-fail-under=85

build:
	uv build
	uv run python scripts/generate_release_artifacts.py

demo:
	uv run continuity demo arctic
	PYTHONPATH=src uv run python scripts/demo.py > /tmp/continuityos-demo.json 2>/dev/null || true

evidence:
	PYTHONPATH=src uv run python scripts/evidence_smoke.py > /tmp/continuityos-evidence.json
	python -m json.tool /tmp/continuityos-evidence.json >/dev/null

iac:
	bash scripts/iac_verify.sh

doctor:
	bash scripts/go_live_doctor.sh

verify: lint typecheck coverage build demo evidence iac

keys:
	uv run continuityos generate-evidence-keys ./secrets

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info var
