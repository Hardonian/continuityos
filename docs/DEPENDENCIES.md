# Dependency Reproducibility

All direct runtime, runtime and verification dependencies are pinned exactly in `pyproject.toml` and `requirements.pinned.txt`.

A fully resolved `uv.lock` should be generated and committed from a trusted package registry before production release:

```bash
uv lock
uv sync --all-extras --frozen
```

During creation of this reference package, the configured package registry returned HTTP 503 while resolving `cryptography`; therefore a transitive lock could not be honestly generated in that environment. Functional verification used the installed versions matching the runtime pins. CI is configured to resolve the pinned direct dependencies and should commit the resulting lock after the first successful trusted run.

For controlled production builds, mirror all wheels internally, verify hashes, generate an SBOM, and build with `--require-hashes` or an equivalent locked mechanism.
