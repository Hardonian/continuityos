from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import cast
from unittest.mock import patch
from urllib.request import Request

import pytest

from continuityos.evidence import EvidenceLedger

_SPEC = importlib.util.spec_from_file_location(
    "strategic_ingest", Path(__file__).parents[1] / "scripts" / "strategic_ingest.py"
)
assert _SPEC is not None and _SPEC.loader is not None
strategic_ingest = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(strategic_ingest)


def _record(ledger: EvidenceLedger, indicator: dict[str, object]) -> None:
    ledger.append(
        "public_data_indicators",
        "source-snapshot",
        {"source_id": "source", "snapshot_ids": ["snapshot"], "indicators": [indicator]},
    )


def _indicator(indicator_id: str = "eccc.alert.ehw", value: float = 1.0) -> dict[str, object]:
    return {
        "indicator_id": indicator_id,
        "observed_at": "2026-07-23T12:00:00Z",
        "value": value,
        "unit": "active_alert_event",
        "source_id": "eccc-geomet-alerts",
        "provenance_snapshot_ids": ["snapshot"],
        "quality_flags": [],
        "metadata": {"confidence": "high"},
    }


def test_loader_preserves_provenance_and_skips_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator())
    _record(ledger, _indicator("unknown.indicator"))
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(strategic_ingest, "env_value", lambda _: "")

    observations, skipped, sources = strategic_ingest.load_observations()

    assert len(observations) == 1
    assert skipped == 1
    assert sources == ["eccc-geomet-alerts"]
    assert observations[0]["provenance"]["content_sha256"]
    assert observations[0]["provenance"]["snapshot_id"] == "snapshot"


def test_loader_is_deterministic_and_deduplicates_exact_replays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator())
    _record(ledger, _indicator())
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(strategic_ingest, "env_value", lambda _: "")

    first, _, _ = strategic_ingest.load_observations()
    second, _, _ = strategic_ingest.load_observations()

    assert first == second
    assert len(first) == 1


def test_loader_fails_closed_on_tampered_hash_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator())
    row = json.loads(ledger_path.read_text())
    row["payload"]["indicators"][0]["value"] = 999
    ledger_path.write_text(json.dumps(row) + "\n")
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(strategic_ingest, "env_value", lambda _: "")

    with pytest.raises(RuntimeError, match="ledger verification failed"):
        strategic_ingest.load_observations()


def test_loader_rejects_invalid_metric_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator("eccc.alert.ehw", float("nan")))
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(strategic_ingest, "env_value", lambda _: "")

    with pytest.raises(RuntimeError, match="ledger verification failed"):
        strategic_ingest.load_observations()


def test_main_requires_api_key_and_does_not_post_without_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator())
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(strategic_ingest, "env_value", lambda _: "")

    with pytest.raises(RuntimeError, match="API_KEY"):
        strategic_ingest.main()


def test_main_posts_bounded_idempotent_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = EvidenceLedger(ledger_path)
    _record(ledger, _indicator())
    monkeypatch.setattr(strategic_ingest, "LEDGER", ledger_path)
    monkeypatch.setattr(
        strategic_ingest,
        "env_value",
        lambda name: "test-key" if name == "CONTINUITYOS_API_KEY" else "",
    )

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"report_id":"report","observation_count":1,"alerts":[]}'

    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: int) -> Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    with patch.object(strategic_ingest.urllib.request, "urlopen", fake_urlopen):
        assert strategic_ingest.main() == 0
    request = cast(Request, captured["request"])
    assert request.headers["Idempotency-key"].startswith("ledger-strategic-")
    assert len(cast(bytes, request.data)) < 100_000
