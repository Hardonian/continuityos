# Dependency Reproducibility

All direct runtime and verification dependencies are pinned exactly in `pyproject.toml`; `uv.lock` is the reproducible resolver lockfile.

A fully resolved `uv.lock` is committed and must be checked in frozen mode:

```bash
uv lock
uv sync --all-extras --frozen
```

The redundant plain-text pin file was removed because it created a second dependency manifest and stale duplicate Dependabot state. CI uses the lockfile and fails if it is out of date.

For controlled production builds, mirror all wheels internally, verify hashes, generate an SBOM, and build with `--require-hashes` or an equivalent locked mechanism.
