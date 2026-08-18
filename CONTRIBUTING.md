# Contributing to ContinuityOS

Thank you for your interest in contributing to **ContinuityOS**, the open-core Resilience-as-Code engine.

---

## Code of Conduct & Safety Directives

1. **Defensive Purpose**: ContinuityOS is designed solely for defensive planning, business continuity, disaster recovery, supply chain resilience, and critical infrastructure protection. Contributions enabling offensive cyber operations, weapon targeting, or autonomous dispatch of consequential assets will be rejected.
2. **Deterministic & Explainable**: Core algorithms (graph analysis, solver compilation, inventory simulation, recovery modeling) must be deterministic and fully explainable with explicit reason codes.
3. **Evidence & Provenance**: All observations and state assertions must preserve origin metadata, cryptographic hashes, and source trust ratings.

---

## Development Setup

ContinuityOS uses [uv](https://astral-sh.github.io/uv/) for fast, reliable Python dependency management.

```bash
# Clone the repository
git clone https://github.com/Hardonian/continuityos.git
cd continuityos

# Install dependencies and pre-commit tooling
uv sync --all-extras

# Run the test suite
uv run pytest

# Check formatting and typing
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

---

## Submitting Pull Requests

1. Ensure all tests pass with $\ge 85\%$ code coverage:
   ```bash
   uv run pytest --cov=continuityos --cov-fail-under=85
   ```
2. Ensure strict type checking passes:
   ```bash
   uv run mypy src
   ```
3. Format code according to repository standards:
   ```bash
   uv run ruff format .
   uv run ruff check --fix .
   ```
4. Include unit tests for all new engines, DSL primitives, or CLI commands.
