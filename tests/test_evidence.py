from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from continuityos.evidence import EvidenceLedger


def test_evidence_ledger_detects_tampering(tmp_path: Path) -> None:
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


def test_evidence_ledger_records_offset_beyond_file(tmp_path: Path) -> None:
    """Offset past the end of the ledger returns empty list."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)
    ledger.append("assessment", "a-1", {"risk": 0.4})
    result = ledger.records(offset=999, limit=10)
    assert result == []


def test_evidence_ledger_records_basic(tmp_path: Path) -> None:
    """records() returns correct records with offset and limit."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)
    ledger.append("type-1", "s-1", {"k": 1})
    ledger.append("type-2", "s-2", {"k": 2})
    ledger.append("type-3", "s-3", {"k": 3})

    all_records = ledger.records(offset=0, limit=100)
    assert len(all_records) == 3

    page = ledger.records(offset=1, limit=1)
    assert len(page) == 1
    assert page[0].record_type == "type-2"


def test_evidence_ledger_records_validation(tmp_path: Path) -> None:
    """records() rejects bad offset/limit values."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)

    with pytest.raises(ValueError):
        ledger.records(offset=-1, limit=10)

    with pytest.raises(ValueError):
        ledger.records(offset=0, limit=0)

    with pytest.raises(ValueError):
        ledger.records(offset=0, limit=1001)


def test_evidence_ledger_empty_verify(tmp_path: Path) -> None:
    """Verifying a non-existent ledger returns no errors."""
    path = tmp_path / "empty-ledger.jsonl"
    ledger = EvidenceLedger(path)
    assert ledger.verify() == []


def test_evidence_ledger_last_hash_multiple_records(tmp_path: Path) -> None:
    """_last_hash correctly reads the last record in a multi-record ledger."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)
    ledger.append("a", "s-1", {"v": 1})
    ledger.append("b", "s-2", {"v": 2})
    r3 = ledger.append("c", "s-3", {"v": 3})

    assert ledger._last_hash() == r3.record_hash
    # Verify the chain is intact
    assert ledger.verify() == []


def test_evidence_ledger_wrong_public_key(tmp_path: Path) -> None:
    """Verification with wrong public key detects signature failure."""
    signing_key = Ed25519PrivateKey.generate()
    wrong_key = Ed25519PrivateKey.generate().public_key()

    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path, private_key=signing_key)
    ledger.append("assessment", "a-1", {"risk": 0.5})

    # Verify with wrong public key
    verifier = EvidenceLedger(path, public_key=wrong_key)
    errors = verifier.verify()
    assert any("signature verification failed" in e for e in errors)


def test_evidence_ledger_unsigned_records(tmp_path: Path) -> None:
    """Unsigned records can be verified without a public key."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)  # No signing key
    ledger.append("assessment", "a-1", {"risk": 0.4})
    ledger.append("plan", "p-1", {"cost": 100})
    assert ledger.verify() == []


def test_evidence_ledger_records_empty_file(tmp_path: Path) -> None:
    """records() on a non-existent file returns empty list."""
    path = tmp_path / "nonexistent.jsonl"
    ledger = EvidenceLedger(path)
    assert ledger.records() == []
