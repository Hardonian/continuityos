from __future__ import annotations

import json
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.evidence import EvidenceLedger


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="continuityos-evidence-") as directory:
        ledger_path = Path(directory) / "ledger.jsonl"
        key = Ed25519PrivateKey.generate()
        ledger = EvidenceLedger(ledger_path, private_key=key)
        first = ledger.append("release_smoke", "continuityos-reference", {"stage": "build"})
        second = ledger.append(
            "release_smoke",
            "continuityos-reference",
            {"stage": "verify", "previous": first.record_id},
        )
        errors = EvidenceLedger(ledger_path, public_key=key.public_key()).verify()
        if errors:
            raise RuntimeError(f"evidence verification failed: {errors}")
        print(
            json.dumps(
                {
                    "valid": True,
                    "records": 2,
                    "last_record_hash": second.record_hash,
                    "signing_key_id": second.signing_key_id,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
