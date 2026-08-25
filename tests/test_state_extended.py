"""Extended unit tests for PersistentState module.

Targets: state.py coverage from 83% → 100%.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from continuityos.state import IdempotencyConflict, PersistentState


def test_state_read_corrupt_json_raises(tmp_path: Path) -> None:
    """Unreadable or malformed JSON raises RuntimeError."""
    state_file = tmp_path / "state.json"
    state_file.write_text("INVALID_JSON_HERE{{{")

    state = PersistentState(state_file)
    with pytest.raises(RuntimeError, match="state file is unreadable"):
        state.get_value("ns", "key")


def test_state_read_non_dict_raises(tmp_path: Path) -> None:
    """State file containing a JSON list/primitive instead of dict raises RuntimeError."""
    state_file = tmp_path / "state.json"
    state_file.write_text('["not", "a", "dict"]')

    state = PersistentState(state_file)
    with pytest.raises(RuntimeError, match="state file must contain an object"):
        state.get_value("ns", "key")


def test_state_idempotent_missing_response_raises(tmp_path: Path) -> None:
    """Idempotency record missing 'response' string field raises RuntimeError."""
    state_file = tmp_path / "state.json"
    state = PersistentState(state_file)

    # Manually inject malformed idempotency entry
    state.set_value("idempotency", "test:key", {"fingerprint": "fp1", "response": 12345})

    with pytest.raises(RuntimeError, match="idempotency record has no response"):
        state.get_idempotent("test", "key", "fp1")


def test_state_idempotent_save_conflict_raises(tmp_path: Path) -> None:
    """Saving with same key but different fingerprint raises IdempotencyConflict."""
    state_file = tmp_path / "state.json"
    state = PersistentState(state_file)

    state.save_idempotent("ns", "k1", "fp_initial", "response_data")

    with pytest.raises(IdempotencyConflict, match="reused for a different request"):
        state.save_idempotent("ns", "k1", "fp_different", "new_response")


def test_state_namespace_not_dict_raises(tmp_path: Path) -> None:
    """Namespace being a non-dict raises RuntimeError on get_value and set_value."""
    state_file = tmp_path / "state.json"
    state_file.write_text('{"bad_ns": "not_a_dict"}')
    state = PersistentState(state_file)

    with pytest.raises(RuntimeError, match="state namespace must contain an object"):
        state.get_value("bad_ns", "key")

    with pytest.raises(RuntimeError, match="state namespace must contain an object"):
        state.set_value("bad_ns", "key", "val")


def test_state_unix_locking_path(tmp_path: Path) -> None:
    """Test the Unix fcntl locking path by mocking sys.platform."""
    state_file = tmp_path / "unix_state.json"
    state = PersistentState(state_file)

    mock_fcntl = MagicMock()
    mock_fcntl.LOCK_EX = 2
    mock_fcntl.LOCK_UN = 8

    with (
        patch.object(sys, "platform", "linux"),
        patch.dict("sys.modules", {"fcntl": mock_fcntl}),
    ):
        with state._lock():
            assert mock_fcntl.flock.call_count == 1
        assert mock_fcntl.flock.call_count == 2


def test_state_claim_sequence_out_of_order(tmp_path: Path) -> None:
    """claim_sequence rejects smaller or equal sequence numbers."""
    state_file = tmp_path / "state.json"
    state = PersistentState(state_file)

    assert state.claim_sequence("T1", "A1", 10) is True
    assert state.claim_sequence("T1", "A1", 10) is False  # duplicate
    assert state.claim_sequence("T1", "A1", 5) is False  # older
    assert state.claim_sequence("T1", "A1", 11) is True  # newer
