#!/usr/bin/env python3
"""Fail-soft watchdog for the ContinuityOS strategic signal surface."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

STATE = Path(
    os.environ.get(
        "CONTINUITYOS_WATCHDOG_STATE",
        "/home/scott/.local/share/continuityos/strategic-watchdog.json",
    )
)
INBOX = Path("/home/scott/ai-lab/reports/operator-inbox.jsonl")
ENV_FILE = Path("/home/scott/.config/continuityos.env")
URL = "http://127.0.0.1:8082/v1/strategic/stream?duration_seconds=1"


def api_key() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(errors="ignore").splitlines():
            if line.startswith("CONTINUITYOS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("CONTINUITYOS_API_KEY", "")


def emit_once(kind: str, severity: str, message: str, evidence: str, action: str) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    if STATE.exists():
        try:
            previous = json.loads(STATE.read_text())
        except (OSError, json.JSONDecodeError):
            previous = {}
    if previous.get("signature") == f"{kind}:{message}":
        return
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "kind": kind,
        "severity": severity,
        "message": message,
        "source": "continuityos-strategic-watchdog",
        "evidence": evidence,
        "action": action,
    }
    with INBOX.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    STATE.write_text(
        json.dumps({"signature": f"{kind}:{message}", "updated_at": record["ts"]}, sort_keys=True)
    )


def clear() -> None:
    if STATE.exists():
        STATE.unlink()


def main() -> int:
    key = api_key()
    if not key:
        emit_once(
            "gate",
            "warn",
            "strategic watchdog missing API key",
            str(ENV_FILE),
            "configure CONTINUITYOS_API_KEY",
        )
        return 0
    request = urllib.request.Request(URL, headers={"X-Continuity-API-Key": key})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = response.read().decode(errors="ignore")
    except (OSError, urllib.error.URLError) as exc:
        emit_once(
            "service_down",
            "critical",
            "strategic stream unavailable",
            URL,
            "check continuityos.service and /readyz",
        )
        print(json.dumps({"status": "down", "error": type(exc).__name__}))
        return 0
    snapshots = [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]
    if not snapshots:
        emit_once(
            "needs_decision",
            "warn",
            "strategic stream has no analysis snapshot",
            URL,
            "ingest current observations before relying on strategic alerts",
        )
        print(json.dumps({"status": "no_snapshot"}))
        return 0
    report = snapshots[-1]
    stale = [
        item.get("source_id", "unknown")
        for item in report.get("source_freshness", [])
        if item.get("stale")
    ]
    if stale:
        emit_once(
            "stale_source",
            "warn",
            "strategic source freshness degraded: " + ",".join(stale),
            URL,
            "refresh or validate the affected source before consequential use",
        )
    else:
        clear()
    print(
        json.dumps(
            {"status": "ok", "report_id": report.get("report_id"), "stale_sources": stale},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
