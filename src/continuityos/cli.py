from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.compiler import ContinuityCompiler
from continuityos.domain import CompileRequest, Observation
from continuityos.evidence import EvidenceLedger
from continuityos.fusion import FusionEngine
from continuityos.sources.cache import SnapshotCache


def _load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        payload: Any
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(handle)
        else:
            payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected an object at document root: {path}")
    return cast(dict[str, Any], payload)


def command_assess(args: argparse.Namespace) -> None:
    payload = _load(args.input)
    observations = [Observation.model_validate(item) for item in payload["observations"]]
    assessment = FusionEngine().assess(payload["corridor_id"], observations)
    print(assessment.model_dump_json(indent=2))


def command_compile(args: argparse.Namespace) -> None:
    request = CompileRequest.model_validate(_load(args.input))
    plan = ContinuityCompiler(args.max_actions).compile(request)
    print(plan.model_dump_json(indent=2))


def command_import_snapshot(args: argparse.Namespace) -> None:
    cache = SnapshotCache(args.cache_dir)
    metadata = cache.import_file(args.source_id, args.uri, args.file, args.content_type)
    print(json.dumps(metadata.__dict__, indent=2, sort_keys=True))


def command_verify_ledger(args: argparse.Namespace) -> None:
    ledger = EvidenceLedger.from_key_files(args.ledger, None, args.public_key)
    errors = ledger.verify()
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    raise SystemExit(0 if not errors else 1)


def command_generate_keys(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_path = args.output_dir / "evidence-private.pem"
    public_path = args.output_dir / "evidence-public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    private_path.chmod(0o600)
    print(json.dumps({"private_key": str(private_path), "public_key": str(public_path)}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="continuityos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess = subparsers.add_parser("assess")
    assess.add_argument("input", type=Path)
    assess.set_defaults(func=command_assess)

    compile_command = subparsers.add_parser("compile")
    compile_command.add_argument("input", type=Path)
    compile_command.add_argument("--max-actions", type=int, default=24)
    compile_command.set_defaults(func=command_compile)

    snapshot = subparsers.add_parser("import-snapshot")
    snapshot.add_argument("--source-id", required=True)
    snapshot.add_argument("--uri", required=True)
    snapshot.add_argument("--file", required=True, type=Path)
    snapshot.add_argument("--content-type")
    snapshot.add_argument("--cache-dir", type=Path, default=Path("./var/snapshots"))
    snapshot.set_defaults(func=command_import_snapshot)

    verify = subparsers.add_parser("verify-ledger")
    verify.add_argument("ledger", type=Path)
    verify.add_argument("--public-key", type=Path)
    verify.set_defaults(func=command_verify_ledger)

    keys = subparsers.add_parser("generate-evidence-keys")
    keys.add_argument("output_dir", type=Path)
    keys.set_defaults(func=command_generate_keys)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
