#!/usr/bin/env python3
"""Convert verified public-data ledger indicators into strategic observations."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from continuityos.domain import AssertionClass, MetricName, Observation, Provenance, SourceTrust
from continuityos.evidence import EvidenceLedger

DATA_DIR = Path(os.environ.get("CONTINUITYOS_DATA_DIR", "/home/scott/.local/share/continuityos"))
LEDGER = DATA_DIR / "evidence" / "ledger.jsonl"
ENV_FILE = Path("/home/scott/.config/continuityos.env")
API_URL = "http://127.0.0.1:8082/v1/strategic/analyze"

MAPPING = {
    "eccc.alert.aqw": (MetricName.WEATHER_ALERT_ACTIVITY, AssertionClass.WEATHER),
    "eccc.alert.ehw": (MetricName.WEATHER_ALERT_ACTIVITY, AssertionClass.WEATHER),
    "eccc.alert.stw": (MetricName.WEATHER_ALERT_ACTIVITY, AssertionClass.WEATHER),
    "cdd.disaster_event": (MetricName.DISASTER_EVENT_ACTIVITY, AssertionClass.DISASTER_RESPONSE),
    "cdd.deaths": (MetricName.CASUALTY_COUNT, AssertionClass.DISASTER_RESPONSE),
    "cdd.injured": (MetricName.INJURED_COUNT, AssertionClass.DISASTER_RESPONSE),
    "cdd.evacuated": (MetricName.EVACUATION_COUNT, AssertionClass.DISASTER_RESPONSE),
    "cdd.utility_people_affected": (
        MetricName.UTILITY_IMPACT_COUNT,
        AssertionClass.DISASTER_RESPONSE,
    ),
    "dfo.iwls.water_level": (MetricName.WATER_LEVEL, AssertionClass.CLIMATE),
}


def env_value(name: str) -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(errors="ignore").splitlines():
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(name, "")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def confidence(indicator: dict[str, object]) -> float:
    metadata = indicator.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    declared = str(metadata.get("confidence", "")).lower()
    if declared == "high":
        return 0.95
    if declared == "moderate":
        return 0.80
    if indicator.get("quality_flags"):
        return 0.60
    return 0.85


def load_observations() -> tuple[list[dict[str, object]], int, list[str]]:
    key_path = env_value("CONTINUITYOS_EVIDENCE_PUBLIC_KEY_PATH")
    public_key = Path(key_path) if key_path else None
    ledger = EvidenceLedger.from_key_files(
        LEDGER, None, public_key if public_key and public_key.exists() else None
    )
    errors = ledger.verify()
    if errors:
        raise RuntimeError("evidence ledger verification failed: " + "; ".join(errors[:3]))
    selected: dict[str, Observation] = {}
    skipped = 0
    sources: set[str] = set()
    for line in LEDGER.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") != "public_data_indicators":
            continue
        payload = record.get("payload", {})
        for indicator in payload.get("indicators", []):
            metric_info = MAPPING.get(str(indicator.get("indicator_id")))
            if metric_info is None:
                skipped += 1
                continue
            metric, assertion = metric_info
            value = float(indicator["value"])
            observed_at = parse_time(str(indicator["observed_at"]))
            source_id = str(indicator["source_id"])
            raw_unit = str(indicator.get("unit", "unknown"))
            unit = "metres" if metric == MetricName.WATER_LEVEL else raw_unit
            snapshot_ids = tuple(str(item) for item in indicator.get("provenance_snapshot_ids", []))
            stable = ":".join(
                [
                    source_id,
                    str(indicator.get("indicator_id")),
                    str(indicator.get("observed_at")),
                    str(indicator.get("value")),
                    json.dumps(indicator.get("metadata", {}), sort_keys=True),
                ]
            )
            observation_key = hashlib.sha256(stable.encode()).hexdigest()
            selected[observation_key] = Observation(
                observation_id=uuid5(NAMESPACE_URL, "continuityos:ledger:" + stable),
                source_id=source_id,
                source_trust=SourceTrust.AUTHORITATIVE_PUBLIC,
                assertion_class=assertion,
                metric=metric,
                value=value,
                unit=unit,
                observed_at=observed_at,
                confidence=confidence(indicator),
                provenance=Provenance(
                    uri=f"ledger://continuityos/{record['record_id']}",
                    retrieved_at=parse_time(str(record["created_at"])),
                    content_sha256=str(record["record_hash"]),
                    snapshot_id=snapshot_ids[0] if snapshot_ids else None,
                ),
                metadata={
                    "indicator_id": str(indicator.get("indicator_id")),
                    "original_unit": raw_unit,
                    "quality_flags": ",".join(
                        str(item) for item in indicator.get("quality_flags", [])
                    ),
                    "source_record_id": str(record["record_id"]),
                },
            )
            sources.add(source_id)
    observations = sorted(selected.values(), key=lambda item: item.observed_at)[-800:]
    return [item.model_dump(mode="json") for item in observations], skipped, sorted(sources)


def main() -> int:
    observations, skipped, sources = load_observations()
    if not observations:
        print(json.dumps({"status": "no_supported_observations", "skipped": skipped}))
        return 0
    request = {
        "observations": observations,
        "alert_threshold": 0.65,
        "coordination_scope": "operator-review",
    }
    body = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    if len(body) > 900_000:
        raise RuntimeError(f"strategic request exceeds safe body budget: {len(body)} bytes")
    idem = hashlib.sha256(body).hexdigest()
    api_key = env_value("CONTINUITYOS_API_KEY")
    if not api_key:
        raise RuntimeError("CONTINUITYOS_API_KEY is not configured")
    http_request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Continuity-API-Key": api_key,
            "Idempotency-Key": "ledger-strategic-" + idem,
        },
    )
    try:
        with urllib.request.urlopen(http_request, timeout=30) as response:
            report = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="ignore")[:500]
        raise RuntimeError(f"strategic analysis HTTP {exc.code}: {detail}") from exc
    print(
        json.dumps(
            {
                "status": "analyzed",
                "report_id": report.get("report_id"),
                "observation_count": report.get("observation_count"),
                "alert_count": len(report.get("alerts", [])),
                "sources": sources,
                "unsupported_indicators_skipped": skipped,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
