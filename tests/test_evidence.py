from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.evidence import EvidenceLedger


def test_evidence_ledger_detects_tampering(tmp_path) -> None:
    private_key = Ed25519PrivateKey.generate()
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path, private_key=private_key)
    ledger.append("assessment", "a-1", {"risk": 0.4})
    ledger.append("plan", "p-1", {"cost": 100})
    assert ledger.verify() == []
    content = path.read_text().replace('"cost":100', '"cost":101')
    path.write_text(content)
    errors = ledger.verify()
    assert any("record hash mismatch" in error for error in errors)
