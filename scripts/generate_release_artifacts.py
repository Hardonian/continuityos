"""Generate SHA256 checksums and SBOM for ContinuityOS v1.0 release artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_checksums(dist_dir: Path, target_version: str = "1.0.0") -> dict[str, str]:
    checksums: dict[str, str] = {}
    lines: list[str] = []

    for file in sorted(dist_dir.glob(f"continuityos-{target_version}*")):
        if file.is_file() and not file.name.endswith(".txt") and not file.name.endswith(".json"):
            digest = compute_sha256(file)
            checksums[file.name] = digest
            lines.append(f"{digest}  {file.name}\n")

    sums_file = dist_dir / "SHA256SUMS.txt"
    sums_file.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote checksums to {sums_file}")
    return checksums


def generate_spdx_sbom(dist_dir: Path, pyproject_path: Path) -> Path:
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    name = project.get("name", "continuityos")
    version = project.get("version", "1.0.0")
    description = project.get("description", "")
    license_id = project.get("license", "Apache-2.0")
    dependencies = project.get("dependencies", [])

    packages: list[dict[str, object]] = [
        {
            "SPDXID": "SPDXRef-Package-ContinuityOS",
            "name": name,
            "versionInfo": version,
            "summary": description,
            "licenseDeclared": license_id,
            "downloadLocation": f"https://github.com/Hardonian/continuityos/releases/tag/v{version}",
            "supplier": "Organization: ContinuityOS Contributors",
        }
    ]

    relationships: list[dict[str, str]] = []

    for i, dep in enumerate(dependencies, start=1):
        dep_clean = dep.split(";")[0].strip()
        dep_name = dep_clean.split("==")[0].split(">=")[0].split("<=")[0].strip()
        dep_version = dep_clean[len(dep_name) :].lstrip("=><~ ") or "any"
        spdx_id = f"SPDXRef-Package-Dep-{i}-{dep_name}"

        packages.append(
            {
                "SPDXID": spdx_id,
                "name": dep_name,
                "versionInfo": dep_version,
                "licenseDeclared": "NOASSERTION",
                "downloadLocation": f"https://pypi.org/project/{dep_name}/",
            }
        )
        relationships.append(
            {
                "spdxElementId": "SPDXRef-Package-ContinuityOS",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": spdx_id,
            }
        )

    spdx_doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{name}-{version}-SBOM",
        "documentNamespace": f"https://continuity.io/spdx/{name}-{version}",
        "creationInfo": {
            "created": "2026-09-07T00:00:00Z",
            "creators": ["Tool: ContinuityOS Release Engine v1.0.0"],
        },
        "packages": packages,
        "relationships": relationships,
    }

    sbom_file = dist_dir / f"{name}-{version}.spdx.json"
    sbom_file.write_text(json.dumps(spdx_doc, indent=2), encoding="utf-8")
    print(f"Wrote SPDX 2.3 SBOM to {sbom_file}")
    return sbom_file


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    dist = root / "dist"
    pyproject = root / "pyproject.toml"

    if not dist.exists():
        dist.mkdir(parents=True, exist_ok=True)

    checksums = generate_checksums(dist)
    for name, digest in checksums.items():
        print(f"  {name}: {digest}")

    generate_spdx_sbom(dist, pyproject)
    print("Release artifacts generated successfully.")


if __name__ == "__main__":
    main()
