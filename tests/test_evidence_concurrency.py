from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.evidence import EvidenceLedger


def test_concurrent_appends_preserve_chain(tmp_path) -> None:
    ledger = EvidenceLedger(tmp_path / "ledger.jsonl", private_key=Ed25519PrivateKey.generate())
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: ledger.append("observation", str(index), {"i": index}),
                range(32),
            )
        )
    assert ledger.verify() == []
    assert len((tmp_path / "ledger.jsonl").read_text().splitlines()) == 32
