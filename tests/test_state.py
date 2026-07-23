from __future__ import annotations

import pytest

from continuityos.state import IdempotencyConflict, PersistentState


def test_idempotency_is_persistent_and_conflicts_on_payload_change(tmp_path) -> None:
    path = tmp_path / "state.json"
    first = PersistentState(path)
    first.save_idempotent("compile", "request-1", "fingerprint-a", '{"plan_id":"1"}')

    second = PersistentState(path)
    assert second.get_idempotent("compile", "request-1", "fingerprint-a") == '{"plan_id":"1"}'
    with pytest.raises(IdempotencyConflict):
        second.get_idempotent("compile", "request-1", "fingerprint-b")


def test_sequence_claim_rejects_replay_and_regression(tmp_path) -> None:
    store = PersistentState(tmp_path / "state.json")
    assert store.claim_sequence("tenant-a", "asset-a", 1) is True
    assert store.claim_sequence("tenant-a", "asset-a", 1) is False
    assert store.claim_sequence("tenant-a", "asset-a", 0) is False
    assert store.claim_sequence("tenant-a", "asset-a", 2) is True
    assert store.claim_sequence("tenant-b", "asset-a", 1) is True
