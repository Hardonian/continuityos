import json
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


def test_evidence_ledger_from_key_files(tmp_path: Path) -> None:
    """from_key_files loads valid Ed25519 PEM keys."""
    from cryptography.hazmat.primitives import serialization

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_path = tmp_path / "priv.pem"
    pub_path = tmp_path / "pub.pem"

    priv_path.write_bytes(
        priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    ledger = EvidenceLedger.from_key_files(tmp_path / "ledger.jsonl", priv_path, pub_path)
    assert ledger.private_key is not None
    assert ledger.public_key is not None


def test_evidence_ledger_from_key_files_non_ed25519(tmp_path: Path) -> None:
    """from_key_files rejects non-Ed25519 keys (e.g. RSA)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub = rsa_priv.public_key()

    priv_path = tmp_path / "rsa_priv.pem"
    pub_path = tmp_path / "rsa_pub.pem"

    priv_path.write_bytes(
        rsa_priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        rsa_pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    with pytest.raises(TypeError, match="private key must be Ed25519"):
        EvidenceLedger.from_key_files(tmp_path / "l.jsonl", priv_path, None)

    with pytest.raises(TypeError, match="public key must be Ed25519"):
        EvidenceLedger.from_key_files(tmp_path / "l.jsonl", None, pub_path)


def test_evidence_ledger_verify_invalid_line_and_missing_pubkey(tmp_path: Path) -> None:
    """verify() catches invalid JSON lines and signed records when no public key is present."""
    priv = Ed25519PrivateKey.generate()
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path, private_key=priv)
    ledger.append("a", "s-1", {"k": 1})

    # Verifying without public key when record is signed reports error
    verifier_no_key = EvidenceLedger(path, public_key=None)
    errors = verifier_no_key.verify()
    assert any("signature present but no public key configured" in e for e in errors)

    # Append invalid JSON line
    with path.open("a") as f:
        f.write("INVALID_JSON\n")

    errors_with_bad_line = ledger.verify()
    assert any("invalid record" in e for e in errors_with_bad_line)


def test_evidence_ledger_verify_previous_hash_mismatch(tmp_path: Path) -> None:
    """verify() catches previous_hash chain breaks."""
    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)
    ledger.append("a", "s-1", {"k": 1})
    ledger.append("b", "s-2", {"k": 2})

    lines = path.read_text().splitlines()
    # Mutate previous_hash in line 2
    rec2 = json.loads(lines[1])
    rec2["previous_hash"] = "f" * 64
    lines[1] = json.dumps(rec2)
    path.write_text("\n".join(lines) + "\n")

    errors = ledger.verify()
    assert any("previous hash mismatch" in e for e in errors)


def test_evidence_ledger_unix_locking(tmp_path: Path) -> None:
    """Test the Unix fcntl locking path in _exclusive_lock."""
    import sys
    from unittest.mock import MagicMock, patch

    path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(path)

    mock_fcntl = MagicMock()
    mock_fcntl.LOCK_EX = 2
    mock_fcntl.LOCK_UN = 8

    with (
        patch.object(sys, "platform", "linux"),
        patch.dict("sys.modules", {"fcntl": mock_fcntl}),
    ):
        with ledger._exclusive_lock():
            assert mock_fcntl.flock.call_count == 1
        assert mock_fcntl.flock.call_count == 2
