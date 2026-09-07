## Description
Briefly describe the purpose of this PR and what problem it solves.

## 10 Core Invariants Verification
Please verify that your PR adheres to the core ContinuityOS invariants:
- [ ] Invariant 1: Physical availability is not equivalent to effective availability.
- [ ] Invariant 2: `UNKNOWN` must never silently become `HEALTHY`.
- [ ] Invariant 3: Preserves observation provenance and cryptographic hashes.
- [ ] Invariant 4: Deterministic evaluation given identical inputs.
- [ ] Invariant 5: Graceful degradation under external provider failure.
- [ ] Invariant 6: Explainable decisions with explicit reason codes.
- [ ] Invariant 7: Explicit correlated failure representation.
- [ ] Invariant 8: Recovery is modeled separately from reopening.
- [ ] Invariant 9: Upstream dependency analysis for nominal redundancy.
- [ ] Invariant 10: Declarative policies remain machine-readable and versionable.

## Defensive Rules of Engagement
- [ ] Does NOT implement offensive cyber operations, weapon targeting, or kinetic dispatch.
- [ ] Preserves human-in-the-loop approval boundaries (all mitigations strictly advisory).

## Quality Gates Checklist
- [ ] `uv run ruff check .` passes without errors.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run mypy src` passes without type errors.
- [ ] `uv run pytest --cov=continuityos --cov-fail-under=85` passes ($\ge 85\%$ coverage).
- [ ] New tests added for new features or bug fixes.
